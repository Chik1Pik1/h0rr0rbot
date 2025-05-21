const { useState, useEffect, useRef } = React;

// Генерация или получение UUID для пользователя
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

  useEffect(() => {
    const signalAudio = document.getElementById('signal-audio');
    const bgAudio = document.getElementById('background-audio');
    
    if (showErrorOverlay) {
      signalAudio.play();
    } else {
      signalAudio.pause(); // Останавливаем signal-audio при скрытии оверлея
      signalAudio.currentTime = 0; // Сбрасываем воспроизведение
    }

    if (showErrorOverlay) {
      setTimeout(() => {
        bgAudio.play();
      }, 3000);
    }
    
    return () => {
      signalAudio.pause(); // Очистка при размонтировании
      bgAudio.pause();
    };
  }, [showErrorOverlay]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!key.trim()) {
      setError('ВВЕДИТЕ КЛЮЧ.');
      return;
    }
    setIsLoading(true);
    setError('Проверка ключа...');
    // Этап 1: Показать ошибку на весь экран
    setShowErrorOverlay(true);
    setTimeout(() => {
      setShowErrorOverlay(false); // Это вызовет остановку signal-audio через useEffect
      // Этап 2: Показать взлом на весь экран
      setShowHackOverlay(true);
      setTimeout(() => {
        setShowHackOverlay(false);
        // Этап 3: Вернуть окно входа
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
      {/* Полноэкранные анимации */}
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
      {/* Окно входа */}
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
  const userId = getUserId();
  const [effects, setEffects] = useState({ 
    blood: false, 
    glitch: false 
  });
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  useEffect(() => {
    return () => {
      document.getElementById('background-audio').pause();
    };
  }, []);

  // Запуск записи
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      
      mediaRecorderRef.current.ondataavailable = (e) => {
        audioChunksRef.current.push(e.data);
      };

      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        await sendVoiceMessage(audioBlob);
        audioChunksRef.current = [];
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
    } catch (err) {
      console.error('Ошибка доступа к микрофону:', err);
    }
  };

  // Отправка голосового сообщения
  const sendVoiceMessage = async (audioBlob) => {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.webm');
    formData.append('user_id', userId);

    try {
      const response = await fetch('/api/voice', {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      setMessages([...messages, { sender: 'user', text: data.text, isVoice: true }]);
    } catch (error) {
      console.error('Ошибка отправки голосового сообщения:', error);
    }
  };

  // Таймер записи
  useEffect(() => {
    let interval;
    if (isRecording) {
      interval = setInterval(() => {
        setRecordingTime((t) => (t >= 60 ? 60 : t + 1));
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isRecording]);

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
      setMessages([...messages, userMessage, { sender: 'demon', text: response.reply }]);
    }
  };

  return (
    <div className="flex flex-col h-full p-4 relative chat-fullscreen">
      <div id="chat-container" className={`chat-container ${isDisconnected ? 'chat-disabled' : ''}`}>
        {messages.map((msg, index) => {
          let text = msg.text;
          if (effects.glitch) {
            text = text.split('').map(c => Math.random() < 0.15 ? '█' : c).join('');
          }
          
          return msg.isVoice ? (
            <div className="voice-message" key={index}>
              <svg className="voice-icon" viewBox="0 0 24 24">
                <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02z"/>
              </svg>
              Голосовое сообщение
            </div>
          ) : (
            <p
              key={index}
              className={`text-xl mb-2 ${msg.sender === 'user' ? 'text-user' : 'text-demon'} ${
                (effects.blood || effects.glitch) ? 'demon-effect' : ''
              }`}
              style={{
                color: effects.blood ? '#ff2222' : '#ff0000',
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
      <form onSubmit={handleSubmit} className="chat-input-form flex">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          className="flex-1 text-user text-xl p-2 border focus:outline-none"
          placeholder="Введи сообщение..."
          disabled={isDisconnected}
        />
        <button
          type="submit"
          className="text-user text-xl border px-4 py-2"
          disabled={isDisconnected}
        >
          Отправить
        </button>
        <div 
          className={`voice-btn ${isRecording ? 'recording' : ''}`}
          onClick={() => {
            if (!isRecording) {
              startRecording();
            } else {
              mediaRecorderRef.current.stop();
              setIsRecording(false);
              setRecordingTime(0);
            }
          }}
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
            <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
          </svg>
        </div>
        {isRecording && (
          <div className="recording-timer">
            {60 - recordingTime}s
          </div>
        )}
      </form>
    </div>
  );
};

ReactDOM.render(<App />, document.getElementById('root'));
