const { useState, useEffect, useRef } = React;

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
    let timeoutId = null;

    // Функция для остановки звука
    const stopSound = () => {
      console.log('Останавливаем errorSound');
      errorSound.pause();
      errorSound.currentTime = 0;
    };

    // Проверка готовности звука перед воспроизведением
    const playSound = () => {
      return new Promise((resolve, reject) => {
        if (errorSound.readyState >= 2) { // HAVE_CURRENT_DATA или выше
          resolve();
        } else {
          errorSound.oncanplay = () => resolve();
          errorSound.onerror = () => reject(new Error('Не удалось загрузить signal-pojarnoy-trevogi.mp3'));
        }
      });
    };

    if (showErrorOverlay) {
      console.log('Запускаем errorSound');
      // Останавливаем звук перед новым воспроизведением
      stopSound();
      playSound()
        .then(() => {
          errorSound.play().catch((e) => {
            console.error('Ошибка воспроизведения signal-pojarnoy-trevogi.mp3:', e);
          });
          // Остановить через 3 секунды
          timeoutId = setTimeout(stopSound, 3000);
        })
        .catch((e) => {
          console.error('Ошибка загрузки звука:', e);
        });
    } else {
      stopSound();
    }

    // Очистка таймера
    return () => {
      if (timeoutId) {
        console.log('Очистка таймера');
        clearTimeout(timeoutId);
      }
      stopSound(); // Дополнительная остановка при размонтировании
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
  const [recordTime, setRecordTime] = useState(0);
  const [hasInteracted, setHasInteracted] = useState(false);
  const userId = getUserId();
  const [effects, setEffects] = useState({ 
    blood: false, 
    glitch: false 
  });
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const timerRef = useRef(null);

  // Фоновый звук из /public/music/
  const backgroundSound = new Audio('/music/fon.mp3');
  backgroundSound.loop = true;

  // Обработчик взаимодействия для фонового звука
  const handleInteraction = () => {
    setHasInteracted(true);
  };

  useEffect(() => {
    const events = ['click', 'touchstart', 'keydown'];
    events.forEach(event => {
      document.addEventListener(event, handleInteraction, { once: true });
    });

    const stopSound = () => {
      console.log('Останавливаем backgroundSound');
      backgroundSound.pause();
      backgroundSound.currentTime = 0;
    };

    const playSound = () => {
      return new Promise((resolve, reject) => {
        console.log('Проверяем готовность fon.mp3, readyState:', backgroundSound.readyState);
        if (backgroundSound.readyState >= 2) {
          resolve();
        } else {
          backgroundSound.oncanplay = () => {
            console.log('fon.mp3 готов к воспроизведению');
            resolve();
          };
          backgroundSound.onerror = () => reject(new Error('Не удалось загрузить fon.mp3'));
          backgroundSound.load();
        }
      });
    };

    const tryPlaySound = () => {
      console.log('Попытка запустить backgroundSound, hasInteracted:', hasInteracted);
      playSound()
        .then(() => {
          backgroundSound.play()
            .then(() => console.log('backgroundSound успешно воспроизводится'))
            .catch((e) => {
              console.error('Ошибка воспроизведения fon.mp3:', e);
              if (!hasInteracted) {
                console.log('Ожидаем взаимодействия пользователя для воспроизведения');
              }
            });
        })
        .catch((e) => {
          console.error('Ошибка загрузки fon.mp3:', e);
        });
    };

    if (hasInteracted) {
      tryPlaySound();
    } else {
      const interactionHandler = () => {
        tryPlaySound();
        events.forEach(event => {
          document.removeEventListener(event, interactionHandler);
        });
      };
      events.forEach(event => {
        document.addEventListener(event, interactionHandler, { once: true });
      });
    }

    return () => {
      stopSound();
      events.forEach(event => {
        document.removeEventListener(event, handleInteraction);
      });
    };
  }, [hasInteracted]);

  // Форматирование времени (MM:SS)
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60).toString().padStart(2, '0');
    const secs = (seconds % 60).toString().padStart(2, '0');
    return `${mins}:${secs}`;
  };

  // Обработчик кнопки микрофона
  const handleMicClick = async () => {
    if (isDisconnected) return;

    if (isRecording) {
      // Остановить запись без отправки
      stopRecording(false);
    } else {
      // Начать запись
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorderRef.current = new MediaRecorder(stream);
        audioChunksRef.current = [];

        mediaRecorderRef.current.ondataavailable = (event) => {
          audioChunksRef.current.push(event.data);
        };

        mediaRecorderRef.current.onstop = (event, shouldSend = true) => {
          if (shouldSend && audioChunksRef.current.length > 0) {
            const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
            const audioUrl = URL.createObjectURL(audioBlob);
            handleAudioSubmit(audioUrl);
          }
          // Очистка потока
          stream.getTracks().forEach(track => track.stop());
        };

        mediaRecorderRef.current.start();
        setIsRecording(true);
        setRecordTime(0);

        // Запуск таймера
        timerRef.current = setInterval(() => {
          setRecordTime(prev => prev + 1);
        }, 1000);

        console.log('Начата запись аудио');
      } catch (error) {
        console.error('Ошибка доступа к микрофону:', error);
        setIsRecording(false);
      }
    }
  };

  // Остановка записи
  const stopRecording = (shouldSend = true) => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop(shouldSend);
      setIsRecording(false);
      clearInterval(timerRef.current);
      console.log('Запись остановлена');
    }
  };

  // Отправка аудио и обработка демоном
  const handleAudioSubmit = async (audioUrl) => {
    if (isDisconnected) return;

    const userMessage = { sender: 'user', audio: audioUrl };
    setMessages([...messages, userMessage]);
    setIsTyping(true);

    // Имитация распознавания речи (заглушка)
    const audioBlob = await fetch(audioUrl).then(res => res.blob());
    const dummyText = 'Привет, это тестовое голосовое сообщение'; // Заменить на реальное распознавание

    try {
      const response = await sendMessage(dummyText);
      setIsTyping(false);

      if (response.isLimitReached) {
        setMessages([...messages, userMessage, { sender: 'demon', text: response.reply }]);
        setIsDisconnected(true);
      } else {
        setMessages([...messages, userMessage, { sender: 'demon', text: response.reply }]);
      }
    } catch (error) {
      setIsTyping(false);
      setMessages([...messages, userMessage, { sender: 'demon', text: 'Я всё ещё здесь... Попробуй снова.' }]);
    }
  };

  // Отправка текстового сообщения
  const sendMessage = async (message) => {
    try {
      const response = await fetch('/api/chat', {
        method='POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, user_id: userId })
      });
      const data = await response.json();
      return data;
    } catch (error) {
      return { reply: 'Я всё ещё здесь... Попробуй снова.', isLimitReached: false, isTimeLimitReached: false };
    }
  };

  const handleTextSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || isDisconnected) return;

    const userMessage = { sender: 'user', text: input };
    setMessages([...messages, userMessage]);
    setInput('');
    setIsTyping(true);

    sendMessage(input).then(response => {
      setIsTyping(false);
      if (response.isLimitReached) {
        setMessages([...messages, userMessage, { sender: 'demon', text: response.reply }]);
        setIsDisconnected(true);
      } else {
        setMessages([...messages, userMessage, { sender: 'demon', text: response.reply }]);
      }
    });
  };

  return (
    <div className="flex flex-col h-full p-4 relative chat-fullscreen">
      <div id="chat-container" className={`chat-container ${isDisconnected ? 'chat-disabled' : ''}`}>
        {messages.map((msg, index) => {
          let text = msg.text;
          if (effects.glitch && msg.text) {
            text = text.split('').map(c => Math.random() < 0.15 ? '█' : c).join('');
          }
          
          return (
            <div key={index} className="mb-2">
              {msg.audio ? (
                <div className={`text-xl ${msg.sender === 'user' ? 'text-user' : 'text-demon'}`}>
                  {msg.sender === 'user' ? '>> ' : '[Сущность #7]: '}
                  <audio src={msg.audio} controls className="inline-block" />
                </div>
              ) : (
                <p
                  className={`text-xl ${msg.sender === 'user' ? 'text-user' : 'text-demon'} ${
                    (effects.blood || effects.glitch) ? 'demon-effect' : ''
                  }`}
                  style={{
                    transform: effects.blood ? 'skew(-2deg)' : 'none'
                  }}
                >
                  {msg.sender === 'user' ? '>> ' : '[Сущность #7]: '}{text}
                </p>
              )}
            </div>
          );
        })}
        {isTyping && !isDisconnected && (
          <p className="text-demon text-xl blink">[Сущность #7]: ...печатает...</p>
        )}
      </div>
      <form onSubmit={handleTextSubmit} className="chat-input-form flex items-center space-x-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          className="text-user text-xl p-2 border focus:outline-none input-field"
          placeholder="Введи сообщение..."
          disabled={isDisconnected || isRecording}
        />
        <button
          type="submit"
          className="text-user text-xl border px-4 py-2"
          disabled={isDisconnected || isRecording}
        >
          Отправить
        </button>
        <div
          className={`mic-button p-2 border ${isRecording ? 'bg-red-600 animate-pulse' : 'text-user'} ${isDisconnected ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
          onClick={handleMicClick}
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-5 w-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
            />
          </svg>
          {isRecording && (
            <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 text-user text-xs font-mono flex items-center">
              <span className="blink mr-1">REC</span>
              <span>{formatTime(recordTime)}</span>
              <span className="ml-1 animate-pulse">|█|</span>
            </div>
          )}
        </div>
      </form>
    </div>
  );
};

ReactDOM.render(<App />, document.getElementById('root'));
