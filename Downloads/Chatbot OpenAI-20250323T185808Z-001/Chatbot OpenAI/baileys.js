import { makeWASocket, useMultiFileAuthState, DisconnectReason, downloadMediaMessage } from 'baileys';
import { Boom } from '@hapi/boom';
import dotenv from 'dotenv';
import axios from 'axios';
import qrcode from 'qrcode-terminal';
import fs from 'fs';
import FormData from 'form-data';
import ffmpeg from 'fluent-ffmpeg';
import ffmpegPath from 'ffmpeg-static';
ffmpeg.setFfmpegPath(ffmpegPath);

dotenv.config();

const OPENAI_CHATBOT_URL = 'http://localhost:5000/chat';
const OPENAI_TRANSCRIPTION_URL = 'https://api.openai.com/v1/audio/transcriptions';
const OPENAI_API_KEY = process.env.OPENAI_API_KEY;
const atendimentosAtivos = new Map(); // Gerencia o status da conversa (ativo/inativo)
const suppressOwnMessage = new Map(); // Flag para suprimir mensagens enviadas automaticamente pela IA
const SEU_NUMERO = '5566996269635@s.whatsapp.net';

async function iniciarWhatsApp() {
    const authPath = 'auth_info';
    const { state, saveCreds } = await useMultiFileAuthState(authPath);
    const sock = makeWASocket({
        auth: state,
        printQRInTerminal: true,
    });

    sock.ev.on('connection.update', (update) => {
        const { connection, lastDisconnect, qr } = update;
        if (qr) {
            console.log("📌 Escaneie este QR Code para conectar:");
            qrcode.generate(qr, { small: true });
        }
        if (connection === 'close') {
            const motivo = lastDisconnect?.error ? new Boom(lastDisconnect.error).output.statusCode : null;
            if (motivo === DisconnectReason.loggedOut || motivo === DisconnectReason.connectionClosed) {
                console.log('❌ Desconectado. Tentando reconectar...');
                if (fs.existsSync(authPath)) fs.rmSync(authPath, { recursive: true });
                setTimeout(() => iniciarWhatsApp(), 2000);
                return;
            }
            console.log('🔄 Tentando reconectar...');
            setTimeout(() => iniciarWhatsApp(), 2000);
        }
        console.log('📡 Estado da conexão:', connection);
    });

    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('messages.upsert', async (msg) => {
        const mensagem = msg.messages[0];
        if (!mensagem?.message) return;

        const originalJid = mensagem.key.remoteJid;
        const chatId = originalJid === SEU_NUMERO && mensagem.key.participant 
            ? mensagem.key.participant 
            : originalJid;
        const enviadoPorVoce = mensagem.key.fromMe;

        // Ignora mensagens de grupo
        if (originalJid.endsWith("@g.us")) {
            console.log("🚫 Mensagem de grupo ignorada.");
            return;
        }

        // Ignora notificações de histórico ou mudanças de identidade
        if (mensagem.message?.protocolMessage || mensagem.message?.historySyncNotification) {
            console.log(`ℹ️ Ignorando notificação de histórico para ${chatId}`);
            return;
        }

        // Se a mensagem for enviada por você (a conta conectada)
        if (enviadoPorVoce && chatId !== SEU_NUMERO) {
            if (suppressOwnMessage.get(chatId)) {
                suppressOwnMessage.delete(chatId);
                return;
            }
            const texto = mensagem.message.conversation || mensagem.message.extendedTextMessage?.text;
            if (texto === "Ativar IA") {
                atendimentosAtivos.set(chatId, { active: true, lastReactivate: Date.now() });
                await sock.sendMessage(chatId, { text: "🤖 IA ativada novamente!" });
                console.log(`✅ IA reativada para ${chatId}`);
            } else {
                const entry = atendimentosAtivos.get(chatId);
                const now = Date.now();
                if (entry && entry.lastReactivate && now - entry.lastReactivate < 3000) {
                    console.log(`ℹ️ Ignorando pausa para ${chatId} devido ao debounce.`);
                } else {
                    atendimentosAtivos.set(chatId, { active: false });
                    console.log(`🛑 Atendimento pausado para ${chatId} (você interagiu manualmente).`);
                }
            }
            return;
        }

        // Se o atendimento estiver pausado, a IA não responde
        if (atendimentosAtivos.has(chatId) && !atendimentosAtivos.get(chatId).active) {
            console.log(`🙅 IA desativada para ${chatId}, aguardando ativação manual.`);
            return;
        }

        // Processa mensagens de áudio
        if (mensagem.message.audioMessage) {
            console.log(`🎙️ Áudio recebido de ${chatId}, transcrevendo...`);
            const transcricao = await transcreverAudio(sock, mensagem);
            if (transcricao) {
                console.log(`📝 Transcrição: ${transcricao}`);
                const resposta = await obterRespostaChatbot(transcricao);
                if (resposta) {
                    suppressOwnMessage.set(chatId, true);
                    await sock.sendMessage(chatId, { text: resposta });
                }
            }
            return;
        }

        // Processa mensagens de texto
        const texto = mensagem.message.conversation || mensagem.message.extendedTextMessage?.text;
        if (texto) {
            console.log(`💬 Mensagem recebida de ${chatId}: ${texto}`);
            const resposta = await obterRespostaChatbot(texto);
            if (resposta) {
                suppressOwnMessage.set(chatId, true);
                await sock.sendMessage(chatId, { text: resposta });
            }
        }
    });

    return sock;
}

async function obterRespostaChatbot(pergunta) {
    try {
        const resposta = await axios.post(OPENAI_CHATBOT_URL, { pergunta });
        return resposta.data.resposta;
    } catch (erro) {
        console.error('❌ Erro ao obter resposta do chatbot:', erro.message);
        return '⚠️ Ocorreu um erro ao processar sua solicitação. Tente novamente mais tarde.';
    }
}

async function transcreverAudio(sock, mensagem) {
    try {
        const audioPath = './temp_audio.ogg';
        const convertedAudioPath = './temp_audio.wav';
        const buffer = await downloadMediaMessage(mensagem, "buffer", {}, { logger: console });
        
        // Salva o buffer como arquivo OGG
        fs.writeFileSync(audioPath, buffer);
        console.log(`✅ Áudio salvo em ${audioPath}. Tamanho: ${fs.statSync(audioPath).size} bytes.`);
        
        // Converte o arquivo de áudio de OGG para WAV
        await new Promise((resolve, reject) => {
            ffmpeg(audioPath)
                .toFormat('wav')
                .on('error', (err) => {
                    console.error("❌ Erro na conversão do áudio:", err.message);
                    reject(err);
                })
                .on('end', () => {
                    console.log("✅ Conversão do áudio concluída.");
                    resolve();
                })
                .save(convertedAudioPath);
        });
        
        // Verifica se o arquivo convertido foi criado corretamente
        if (!fs.existsSync(convertedAudioPath)) {
            console.error("❌ Arquivo convertido não encontrado.");
            throw new Error("Falha na conversão do áudio.");
        }
        console.log(`✅ Arquivo convertido em ${convertedAudioPath}. Tamanho: ${fs.statSync(convertedAudioPath).size} bytes.`);
        
        const formData = new FormData();
        formData.append("file", fs.createReadStream(convertedAudioPath));
        formData.append("model", "whisper-1");
        
        const response = await axios.post(OPENAI_TRANSCRIPTION_URL, formData, {
            headers: {
                "Authorization": `Bearer ${OPENAI_API_KEY}`,
                ...formData.getHeaders()
            }
        });
        
        // Remove arquivos temporários
        fs.unlinkSync(audioPath);
        fs.unlinkSync(convertedAudioPath);
        
        return response.data.text;
    } catch (erro) {
        console.error('❌ Erro ao transcrever áudio:', erro.message);
        return '⚠️ Não foi possível transcrever o áudio.';
    }
}

iniciarWhatsApp().catch((erro) => {
    console.error('❌ Erro ao iniciar o WhatsApp:', erro);
});
