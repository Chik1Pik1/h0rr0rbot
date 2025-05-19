const { useState, useEffect } = React;

// Generate or retrieve UUID for user
const getUserId = () => {
  let userId = localStorage.getItem('user_id');
  if (!userId) {
    userId = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      const r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
    localStorage.setItem('user_id', userId);
  }
  return userId;
};

const App = () => {
  const [isAccessGranted, setIsAccessGranted] = useState(false);

  return (
    <div className="root-container">
      {isAccessGranted ? (
        <ChatScreen />
      ) : (
        <AccessScreen onAccessGranted={() => setIsAccessGranted(true)} />
      )}
    </div>
  );
};

const AccessScreen = ({ onAccessGranted }) => {
  const [key, setKey] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showErrorOverlay, setShowErrorOverlay] = useState(false);
  const [showHackOverlay, setShowHackOverlay] = useState(false);

  // Воспроизведение звука ошибки
  useEffect(() => {
    if (showErrorOverlay) {
      const errorSound = new Audio('/music/signal-pojarnoy-trevogi.mp3');
      errorSound.play();
      const timer = setTimeout(() => {
        errorSound.pause();
        errorSound.currentTime = 0;
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [showErrorOverlay]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!key.trim()) {
      setError('ВВЕДИТЕ КЛЮЧ.');
      return;
    }
    setIsLoading(true);
    setError('Проверка ключа...');
    setShowErrorOverlay(true);
    setTimeout(() => {
      setShowErrorOverlay(false);
      setShowHackOverlay(true);
      setTimeout(() => {
        setShowHackOverlay(false);
        setError('ОШИБКА: КЛЮЧ НЕВЕРЕН.\nАКТИВИРОВАН ПРОТОКОЛ «ГОРДЕЕВ»...\n\nWARNING: СИСТЕМА ЗАГРУЖАЕТ РЕЗЕРВНЫЙ КАНАЛ.\nПОДКЛЮЧЕНИЕ К СУЩНОСТИ #7... УСПЕШНО.');
        setTimeout(() => onAccessGranted(), 2000);
      }, 4000);
    }, 3000);
  };

  const generateHackCode = () => {
    const snippets = [
      'INITIALIZE BACKDOOR: 0xDEADBEEF',
      'BYPASS FIREWALL: EXEC 0xFF',
      'INJECT PAYLOAD: SYS_CALL 0x80',
      'OVERRIDE: 10101010 11110000',
      'ROOTKIT DEPLOY: ptr=0xCAFEBABE',
      'CRYPTO BREACH: AES-256 CRACK',
      'SHADOW PROTOCOL: jmp 0xFF34',
      'GHOST THREAD: fork() EXPLOIT',
      'MEM LEAK: 0x7F3A 48B2 MOV AX',
      'NEURAL HACK: 0xFF34 INIT'
    ];
    const codes = [];
    for (let i = 0; i < 30; i++) {
      const top = Math.random() * 100;
      const left = Math.random() * 100;
      const duration = 1 + Math.random() * 2;
      const delay = Math.random() * 2;
      codes.push(
        <div
          key={i}
          className="hack-code"
          style={{
            top: `${top}%`,
            left: `${left}%`,
            animationDuration: `${duration}s`,
            animationDelay: `${delay}s`
          }}
        >
          {snippets[Math.floor(Math.random() * snippets.length)]}
        </div>
      );
    }
    return codes;
  };

  return (
    <>
      {showErrorOverlay && (
        <div className="error-overlay-fullscreen">
          ВНИМАНИЕ! ОШИБКА!
        </div>
      )}
      {showHackOverlay && (
        <div className="hack-overlay-fullscreen">
          <div className="matrix-rain" />
          {generateHackCode()}
        </div>
      )}
      <div className="crt-window">
        <div className="flex flex-col items-center justify-center h-full text-center">
          <h1 className="text-3xl text-demon mb-2 dash-line">СИСТЕМА «ЗЕРКАЛО-1» ────────────────</h1>
          <p className="text-xl text-demon mb-2">ДОСТУП К СУЩНОСТЯМ ЗАПРЕЩЁН.</p>
          <p className="text-xl text-demon mb-4">ГРИФ «СОВ.СЕКРЕТНО»: КГБ-784-ДА</p>
          <form onSubmit={handleSubmit} className="w-full max-w-sm">
            <div className="flex items-center mb-4">
              <label className="text-xl text-demon mr-2">ВВЕДИТЕ КЛЮЧ ДОСТУПА:</label>
              <input
                type="text"
                value={key}
                onChange={(e) => setKey(e.target.value)}
                className="flex-1 text-user text-xl p-2 border focus:outline-none"
                placeholder="_________"
                disabled={isLoading}
              />
            </div>
            <button
              type="submit"
              className="w-full text-user text-xl border px-4 py-2"
              disabled={isLoading}
            >
              Подтвердить
            </button>
          </form>
          {error && (
            <p className="text-demon text-xl mt-4 blink" style={{ whiteSpace: 'pre-line' }}>
              {error}
            </p>
          )}
        </div>
      </div>
    </>
  );
};

const ChatScreen = () => {
  const [messages, setMessages] = useState([
    { sender: 'demon', text: 'Ты кто? Я вижу тебя... через твое устройство.' }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isDisconnected, setIsDisconnected] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const userId = getUserId();
  const [effects, setEffects] = useState({ 
    blood: false, 
    glitch: false 
  });

  // Фоновая музыка
  useEffect(() => {
    const backgroundMusic = new Audio('/music/fon.mp3');
    backgroundMusic.loop = true;
    backgroundMusic.volume = 0.3;
    backgroundMusic.play().catch(() => {});
    return () => {
      backgroundMusic.pause();
      backgroundMusic.currentTime = 0;
    };
  }, []);

  // Таймер записи
  useEffect(() => {
    let timer;
    if (isRecording) {
      timer = setInterval(() => {
        setRecordingTime((prev) => prev + 1);
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [isRecording]);

  // Начать запись
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const chunks = [];

      recorder.ondataavailable = (e) => chunks.push(e.data);
      recorder.onstop = async () => {
        const blob = new Blob(chunks, { type: 'audio/webm' });
        stream.getTracks().forEach(track => track.stop());
        await sendVoiceMessage(blob);
      };

      setMediaRecorder(recorder);
      setIsRecording(true);
      setRecordingTime(0);
      recorder.start();
    } catch (error) {
      console.error('Ошибка записи:', error);
      setMessages([...messages, { sender: 'demon', text: 'Ошибка доступа к микрофону.' }]);
    }
  };

  // Остановить запись
  const stopRecording = () => {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop();
      setIsRecording(false);
    }
  };

  // Отправка голосового сообщения
  const sendVoiceMessage = async (blob) => {
    try {
      const formData = new FormData();
      formData.append('audio', blob, 'voice.webm');
      formData.append('user_id', userId);

      const response = await fetch('/api/voice', {
        method: 'POST',
        body: formData
      });
      const data = await response.json();

      const userMessage = { sender: 'user', text: data.transcription || 'Голосовое сообщение' };
      setMessages([...messages, userMessage]);
      setIsTyping(true);

      const chatResponse = await sendMessage(data.transcription);
      setIsTyping(false);

      if (chatResponse.isLimitReached) {
        setMessages([...messages, userMessage, { sender: 'demon', text: chatResponse.reply }]);
        setIsDisconnected(true);
      } else {
        setMessages([...messages, userMessage, { sender: 'demon', text: chatResponse.reply }]);
      }
    } catch (error) {
      setMessages([...messages, { sender: 'demon', text: 'Ошибка обработки голосового сообщения.' }]);
    }
  };

  // Отправка текстового сообщения
  const sendMessage = async (message) => {
    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, user_id: userId })
      });
      const data = await response.json();
      return data;
    } catch (error) {
      return { reply: 'Я всё ещё здесь... Попробуй снова.', isLimitReached: false, isTimeLimitReached: false };
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || isDisconnected) return;

    const userMessage = { sender: 'user', text: input };
    setMessages([...messages, userMessage]);
    setInput('');
    setIsTyping(true);

    const response = await sendMessage(input);
    setIsTyping(false);

    if (response.isLimitReached) {
      setMessages([...messages, userMessage, { sender: 'demon', text: response.reply }]);
      setIsDisconnected(true);
    } else {
      setMessages([...messages, userMessage, { sender: 'demon', text: chatResponse.reply }]);
      setIsDisconnected(true);
    } else {
      setMessages([...messages, userMessage, { sender: 'demon', text: response.reply }]);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
  };

  return (
    <div className="flex flex-col h-full p-4 relative chat-fullscreen">
      <div id="chat-container" className={`chat-container ${isDisconnected ? 'chat-disabled' : ''}`}>
        {messages.map((msg, index) => {
          let text = msg.text;
          if (effects.glitch) {
            text = text.split('').map(c => Math.random() < 0.15 ? '█' : c).join('');
          }
          
          return (
            <p
              key={index}
              className={`text-xl mb-2 ${msg.sender === 'user' ? 'text-user' : 'text-demon'} ${
                (effects.blood || effects.glitch) ? 'demon-effect' : ''
              }`}
              style={{
                color: effects.blood ? '#ff2222' : msg.sender === 'user' ? '#00FF00' : '#ff0000',
                transform: effects.blood ? 'skew(-2deg)' : 'none'
              }}
            >
              {msg.sender === 'user' ? '>> ' : '[Сущность #7]: '}{text}
            </p>
          );
        })}
        {isTyping && !isDisconnected && (
          <p className="text-demon text-xl blink">[Сущность #7]: ...печатает...</p>
        )}
      </div>
      <form onSubmit={handleSubmit} className="chat-input-form flex items-center">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          className="flex-1 text-user text-xl p-2 border focus:outline-none"
          placeholder="Введи сообщение..."
          disabled={isDisconnected || isRecording}
        />
        <button
          type="submit"
          className="text-user text-xl border px-4 py-2 mx-2"
          disabled={isDisconnected || isRecording || !input.trim()}
        >
          Отправить
        </button>
        <button
          type="button"
          className={`text-user text-xl border px-4 py-2 ${isRecording ? 'stop-button' : 'mic-button'}`}
          onClick={isRecording ? stopRecording : startRecording}
          disabled={isDisconnected}
        >
          {isRecording ? (
            <svg viewBox="0 0 24 24">
              <rect x="4" y="4" width="16" height="16" />
              <text x="12" y="24" fill="#00FF00" fontSize="8" textAnchor="middle">{formatTime(recordingTime)}</text>
            </svg>
          ) : (
            <svg viewBox="0 0 24 24">
              <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
              <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.47 6 6.93V21h2v-3.07c3.39-.46 6-3.4 6-6.93h-2z"/>
            </svg>
          )}
        </button>
      </form>
    </div>
  );
};

ReactDOM.render(<App />, document.getElementById('root'));
