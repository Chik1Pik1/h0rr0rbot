```javascript
const { useState, useEffect } = React;

const App = () => {
  const [isAccessGranted, setIsAccessGranted] = useState(false);

  return (
    <div className={isAccessGranted ? "chat-fullscreen" : "crt-window"}>
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

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!key.trim()) {
      setError('ВВЕДИТЕ КЛЮЧ.');
      return;
    }
    setIsLoading(true);
    setError('Проверка ключа...');
    setTimeout(() => {
      setShowErrorOverlay(true);
      setTimeout(() => {
        setShowErrorOverlay(false);
        setShowHackOverlay(true);
        setTimeout(() => {
          setShowHackOverlay(false);
          setError('ОШИБКА: КЛЮЧ НЕВЕРЕН.\nАКТИВИРОВАН ПРОТОКОЛ «ГОРДЕЕВ»...\n\nWARNING: СИСТЕМА ЗАГРУЖАЕТ РЕЗЕРВНЫЙ КАНАЛ.\nПОДКЛЮЧЕНИЕ К СУЩНОСТИ #7... УСПЕШНО.');
          setTimeout(() => onAccessGranted(), 2000);
        }, 4000); // Длительность анимации взлома
      }, 3000); // Длительность анимации ошибки
    }, 3000); // Задержка перед анимацией
  };

  // Генерация случайных кусков кода для анимации взлома
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
      const duration = 1 + Math.random() * 2; // 1–3 секунды
      const delay = Math.random() * 2; // Случайная задержка
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
    <div className="flex flex-col items-center justify-center h-full text-center">
      {showErrorOverlay && (
        <div className="error-overlay">
          ВНИМАНИЕ! ОШИБКА!
        </div>
      )}
      {showHackOverlay && (
        <div className="hack-overlay">
          <div className="matrix-rain" />
          {generateHackCode()}
        </div>
      )}
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
  );
};

const ChatScreen = () => {
  const [messages, setMessages] = useState([
    { sender: 'demon', text: 'Ты кто? Я вижу тебя... через твое устройство.' }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  // Проверка prefers-reduced-motion
  const isReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Эффекты касания
  useEffect(() => {
    if (isReducedMotion) return;

    let touchTimer;
    const messageElements = document.querySelectorAll('.message');

    const handleTouchStart = function(e) {
      touchTimer = setTimeout(() => {
        this.classList.add('glitch');
        addScratches();
      }, 1500);
    };

    const handleTouchEnd = function() {
      clearTimeout(touchTimer);
      this.classList.remove('glitch');
    };

    messageElements.forEach(msg => {
      msg.addEventListener('touchstart', handleTouchStart);
      msg.addEventListener('touchend', handleTouchEnd);
    });

    return () => {
      messageElements.forEach(msg => {
        msg.removeEventListener('touchstart', handleTouchStart);
        msg.removeEventListener('touchend', handleTouchEnd);
      });
    };
  }, [messages]);

  // Шлейфы при скролле
  useEffect(() => {
    if (isReducedMotion) return;

    let lastScroll = 0;
    const handleScroll = () => {
      const now = Date.now();
      if (now - lastScroll > 100) {
        const lastMessage = document.querySelector('.message:last-child');
        if (lastMessage) {
          const trail = document.createElement('div');
          trail.className = 'shadow-trail';
          lastMessage.appendChild(trail);
          setTimeout(() => trail.remove(), 700);
        }
        lastScroll = now;
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Случайные силуэты (1 раз за сессию)
  useEffect(() => {
    if (isReducedMotion) return;

    let hasSilhouetteAppeared = false;
    if (!hasSilhouetteAppeared) {
      const timeout = setTimeout(() => {
        const ghost = document.createElement('div');
        ghost.className = 'silhouette';
        ghost.style.top = `${Math.random() * 80}vh`;
        ghost.style.left = `${Math.random() * 80}vw`;
        document.body.appendChild(ghost);
        setTimeout(() => ghost.remove(), 500);
        hasSilhouetteAppeared = true;
      }, 120000); // Через 2 минуты
      return () => clearTimeout(timeout);
    }
  }, []);

  const addScratches = () => {
    if (isReducedMotion) return;

    const scratches = document.createElement('div');
    scratches.innerHTML = `
      <div class="scratch top"></div>
      <div class="scratch right"></div>
      <div class="scratch bottom"></div>
    `;
    scratches.className = 'scratches';
    document.body.appendChild(scratches);
    setTimeout(() => scratches.remove(), 500);
  };

  const sendMessage = async (message) => {
    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message })
      });
      const data = await response.json();
      return data.reply;
    } catch (error) {
      return 'Я всё ещё здесь... Попробуй снова.';
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = { sender: 'user', text: input };
    setMessages([...messages, userMessage]);
    setInput('');
    setIsTyping(true);

    const demonReply = await sendMessage(input);
    setIsTyping(false);
    setMessages((prev) => [...prev, { sender: 'demon', text: demonReply }]);
  };

  return (
    <div className="flex flex-col h-full p-4 relative">
      <div className="chat-container">
        {messages.map((msg, index) => (
          <p
            key={index}
            className={`text-xl mb-2 message ${msg.sender === 'user' ? 'text-user' : 'text-demon'}`}
          >
            {msg.sender === 'user' ? '>> ' : '[Сущность #7]: '}{msg.text}
          </p>
        ))}
        {isTyping && (
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
        />
        <button
          type="submit"
          className="text-user text-xl border px-4 py-2"
        >
          Отправить
        </button>
      </form>
    </div>
  );
};

ReactDOM.render(<App />, document.getElementById('root'));
```
