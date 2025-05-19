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

  // Звук сирены для оверлея ошибки из /public/music/
  const errorSound = new Audio('/music/signal-pojarnoy-trevogi.mp3');
  errorSound.loop = false;

  useEffect(() => {
    let timeoutId;
    if (showErrorOverlay) {
      errorSound.play().catch((e) => console.error('Ошибка воспроизведения signal-pojarnoy-trevogi.mp3:', e));
      // Остановить звук через 3 секунды, синхронизированно с оверлеем
      timeoutId = setTimeout(() => {
        errorSound.pause();
        errorSound.currentTime = 0;
      }, 3000);
    } else {
      errorSound.pause();
      errorSound.currentTime = 0;
    }
    // Очистка таймера при размонтировании или изменении showErrorOverlay
    return () => {
      if (timeoutId) clearTimeout(timeoutId);
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
            left: `${top}%`,
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
  const [recognitionError, setRecognitionError] = useState('');
  const userId = getUserId();
  const [effects, setEffects] = useState({ 
    blood: false, 
    glitch: false 
  });

  // Фоновый звук из /public/music/
  const backgroundSound = new Audio('/music/fon.mp3');
  backgroundSound.loop = true;
  backgroundSound.volume = 0.2;

  useEffect(() => {
    backgroundSound.play().catch((e) => console.error('Ошибка воспроизведения fon.mp3:', e));
    return () => {
      backgroundSound.pause();
      backgroundSound.currentTime = 0;
    };
  }, []);

  // Инициализация SpeechRecognition
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const recognition = SpeechRecognition ? new SpeechRecognition() : null;

  if (recognition) {
    recognition.lang = 'ru-RU';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
  }

  // Обработка голосового ввода
  const handleVoiceInput = () => {
    if (!recognition) {
      setRecognitionError('Голосовой ввод не поддерживается в этом браузере.');
      return;
    }

    if (isRecording) {
      recognition.stop();
      setIsRecording(false);
      return;
    }

    setIsRecording(true);
    setRecognitionError('');
    recognition.start();

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setIsRecording(false);
      if (transcript.trim()) {
        handleMessageSubmit(transcript);
      }
    };

    recognition.onerror = (event) => {
      setIsRecording(false);
      setRecognitionError(`Ошибка распознавания: ${event.error}`);
    };

    recognition.onend = () => {
      setIsRecording(false);
    };
  };

  // Отправка сообщения
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

  const handleMessageSubmit = async (message) => {
    if (!message.trim() || isDisconnected) return;

    const userMessage = { sender: 'user', text: message };
    setMessages([...messages, userMessage]);
    setInput('');
    setIsTyping(true);

    const response = await sendMessage(message);
    setIsTyping(false);

    if (response.isLimitReached) {
      setMessages([...messages, userMessage, { sender: 'demon', text: response.reply }]);
      setIsDisconnected(true);
    } else {
      setMessages([...messages, userMessage, { sender: 'demon', text: response.reply }]);
    }
  };

  const handleTextSubmit = (e) => {
    e.preventDefault();
    handleMessageSubmit(input);
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
        {recognitionError && (
          <p className="text-demon text-xl mt-2">{recognitionError}</p>
        )}
      </div>
      <form onSubmit={handleTextSubmit} className="chat-input-form flex">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          className="flex-1 text-user text-xl p-2 border focus:outline-none"
          placeholder="Введи сообщение..."
          disabled={isDisconnected || isRecording}
        />
        <button
          type="button"
          onClick={handleVoiceInput}
          className={`text-user text-xl border px-4 py-2 ${isRecording ? 'bg-red-600' : ''}`}
          disabled={isDisconnected}
        >
          {isRecording ? 'Стоп' : 'Голос'}
        </button>
        <button
          type="submit"
          className="text-user text-xl border px-4 py-2"
          disabled={isDisconnected || isRecording}
        >
          Отправить
        </button>
      </form>
    </div>
  );
};

ReactDOM.render(<App />, document.getElementById('root'));
