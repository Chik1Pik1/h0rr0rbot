const { useState, useEffect } = React;

// Аудио контекст для управления звуком
const AudioContext = React.createContext(null);

// Список всех возможных ключей
const DEMON_KEYS = [
  "Astaroth", "Baphomet", "Choronzon", "Dantalion", "Eligos", "Furfur", "Gremory", 
  "Haagenti", "Incubus", "Jinn", "Kobold", "Leviathan", "Mammon", "Naberius", 
  "Oriax", "Paimon", "Raum", "Samael", "Tannin", "Ukobach", "Valac", "Wendigo", 
  "Xaphan", "Yaksha", "Zagan", "Necronomicon", "Goetia", "Qliphoth", "ArsGoetia", 
  "Azazel", "Belial", "Beelzebub", "Asmodeus", "Lilith", "Moloch", "Abaddon", 
  "Amon", "Andras", "Agares", "Barbatos", "Buer", "Caim", "Decarabia", "Forneus", 
  "Gamigin", "Ipos", "Leraje", "Malphas", "Orobas", "Phenex", "Ronove", "Sabnock", 
  "Seere", "Shax", "Stolas", "Vepar", "Zepar", "Nyarlathotep", "Cthulhu", 
  "YogSothoth", "Dagon", "ShubNiggurath", "Akuma", "Oni", "Kitsune", "Djinn", 
  "Ifrit", "Marid", "Ghul", "Dybbuk", "Nephilim", "Grigori", "Archon", "Aeon", 
  "Egregore", "Goetic", "Enochian", "Theurgy", "Necromancy", "Thaumaturgy", 
  "Solomonic", "Hexagram", "Pentacle", "Sigil", "Abraxas", "Akasha", "Chthonic", 
  "Erebus", "Hecate", "Infernal", "Lemegethon", "Mephisto", "Pandemonium", 
  "Stygian", "Tartarus", "Zoroaster", "Banshee", "Doppelganger", "Poltergeist", 
  "Wraith", "Shadowman", "Skinwalker", "Wendigo", "Ouija", "Exorcism", 
  "Possession", "Divination", "Scrying", "Familiar", "Coven", "Sabbat", 
  "Akelarre", "Athame", "Boline", "Chalice", "Grimoire", "Mandrake", "Obsidian", 
  "Runes", "Talisman", "Vortex", "Ziggurat", "BlackMass", "BloodPact", 
  "DarkRite", "Infernum", "Nocturnal", "Occultus", "Phantasm", "Seraphim", 
  "Tenebrae", "Umbra", "Voodoo", "Witching", "Xibalba", "Yatagarasu", 
  "Zephyrus", "Maleficium", "Strigoi", "Karcist", "Qlippoth", "Sephirot", 
  "Demogorgon", "Nyx", "Erebos", "Hypnos", "Moros", "Oneiroi", "Thanatos", "Lethe"
];

// Провайдер для управления аудио
const AudioProvider = ({ children }) => {
  const [signalAudio, setSignalAudio] = useState(null);
  const [backgroundAudio, setBackgroundAudio] = useState(null);

  useEffect(() => {
    // Создаем аудио элементы
    const signal = new Audio('/music/signal.mp3');
    const background = new Audio('/music/fon.mp3');
    
    // Настраиваем фоновую музыку
    background.loop = true;
    background.volume = 1.0; // Громкость 100%
    
    setSignalAudio(signal);
    setBackgroundAudio(background);

    // Очистка при размонтировании
    return () => {
      signal.pause();
      background.pause();
    };
  }, []);

  return (
    <AudioContext.Provider value={{ signalAudio, backgroundAudio }}>
      {children}
    </AudioContext.Provider>
  );
};

// Генерация ежедневного ключа
const generateDailyKey = () => {
  const date = "2025-05-22"; // Фиксированная дата
  const USER_LOGIN = "Chik1Pik1"; // Фиксированный логин
  
  const SALT = USER_LOGIN.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
  let seed = date.split('-').reduce((acc, num) => acc + parseInt(num), 0);
  seed = (seed * SALT) % DEMON_KEYS.length;
  
  return DEMON_KEYS[seed];
};

// Функции для работы с попытками входа
const getAttemptsLeft = () => {
  return parseInt(localStorage.getItem('attemptsLeft') || '3');
};

const setAttemptsLeft = (attempts) => {
  localStorage.setItem('attemptsLeft', attempts.toString());
};

const getBlockedUntil = () => {
  return localStorage.getItem('blockedUntil') || '';
};

const setBlockedUntil = (date) => {
  localStorage.setItem('blockedUntil', date);
};

// Форматирование даты и времени
const formatDateTime = (date) => {
  return date.toLocaleString('ru-RU', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  }).replace(',', '');
};

// Генерация или получение UUID пользователя
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

// Основной компонент приложения
const App = () => {
  const [isAccessGranted, setIsAccessGranted] = useState(false);

  return (
    <AudioProvider>
      <div className="root-container">
        {isAccessGranted ? (
          <ChatScreen />
        ) : (
          <AccessScreen onAccessGranted={() => setIsAccessGranted(true)} />
        )}
      </div>
    </AudioProvider>
  );
};

// Экран доступа
const AccessScreen = ({ onAccessGranted }) => {
  const { signalAudio } = React.useContext(AudioContext);
  const [key, setKey] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showErrorOverlay, setShowErrorOverlay] = useState(false);
  const [showHackOverlay, setShowHackOverlay] = useState(false);
  const [attemptsLeft, setAttempts] = useState(getAttemptsLeft());

  // Проверка блокировки при загрузке
  useEffect(() => {
    const blockedUntil = getBlockedUntil();
    if (blockedUntil) {
      const blockDate = new Date(blockedUntil);
      if (blockDate > new Date()) {
        setError(`ДОСТУП ЗАБЛОКИРОВАН.\nПОВТОРИТЕ ПОПЫТКУ ПОСЛЕ: ${formatDateTime(blockDate)}`);
        setAttempts(0);
      } else {
        localStorage.removeItem('blockedUntil');
        setAttemptsLeft(3);
        setAttempts(3);
      }
    }
  }, []);

  // Генерация кода для эффекта взлома
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

  // Обработка отправки формы
  const handleSubmit = (e) => {
    e.preventDefault();
    if (!key.trim() || attemptsLeft <= 0) return;

    setIsLoading(true);
    setError('Проверка ключа...');

    const correctKey = generateDailyKey();
    
    if (key === correctKey) {
      setShowErrorOverlay(true);
      if (signalAudio) {
        signalAudio.currentTime = 0;
        signalAudio.play();
      }

      setAttemptsLeft(3);
      localStorage.removeItem('blockedUntil');

      setTimeout(() => {
        setShowErrorOverlay(false);
        if (signalAudio) {
          signalAudio.pause();
        }
        setShowHackOverlay(true);
        setTimeout(() => {
          setShowHackOverlay(false);
          setError('ОШИБКА: КЛЮЧ НЕВЕРЕН.\nАКТИВИРОВАН ПРОТОКОЛ «ГОРДЕЕВ»...\n\nWARNING: СИСТЕМА ЗАГРУЖАЕТ РЕЗЕРВНЫЙ КАНАЛ.\n[...]');
          setTimeout(() => onAccessGranted(), 2000);
        }, 4000);
      }, 3000);
    } else {
      const newAttempts = attemptsLeft - 1;
      setAttempts(newAttempts);
      setAttemptsLeft(newAttempts);
      
      if (newAttempts <= 0) {
        const blockUntil = new Date(Date.now() + 24 * 60 * 60 * 1000);
        setBlockedUntil(blockUntil.toISOString());
        const formattedDate = formatDateTime(blockUntil);
        setError(`ДОСТУП ЗАБЛОКИРОВАН.\nПОВТОРИТЕ ПОПЫТКУ ПОСЛЕ: ${formattedDate}`);
      } else {
        setError(`НЕВЕРНЫЙ КЛЮЧ. ОСТАЛОСЬ ПОПЫТОК: ${newAttempts}`);
      }
      setIsLoading(false);
    }
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
          {attemptsLeft > 0 ? (
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
                  style={{ color: '#00ff00', borderColor: '#00ff00' }}
                />
              </div>
              <button
                type="submit"
                className="w-full text-user text-xl border px-4 py-2"
                disabled={isLoading}
                style={{ color: '#00ff00', borderColor: '#00ff00' }}
              >
                Подтвердить
              </button>
              <p className="text-demon text-xl mt-2">
                Осталось попыток: {attemptsLeft}
              </p>
            </form>
          ) : (
            <p className="text-demon text-xl mt-4 blink">ДОСТУП ЗАБЛОКИРОВАН</p>
          )}
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

// Экран чата
const ChatScreen = () => {
  const { backgroundAudio } = React.useContext(AudioContext);
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

  // Управление фоновой музыкой
  useEffect(() => {
    if (backgroundAudio) {
      backgroundAudio.play().catch(error => {
        console.log('Ошибка воспроизведения фоновой музыки:', error);
      });
    }
    return () => {
      if (backgroundAudio) {
        backgroundAudio.pause();
        backgroundAudio.currentTime = 0;
      }
    };
  }, [backgroundAudio]);

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

  // Обработка отправки сообщения
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
          
          const messageStyle = {
            color: msg.sender === 'user' ? '#00ff00' : (effects.blood ? '#ff2222' : '#ff0000'),
            transform: effects.blood ? 'skew(-2deg)' : 'none'
          };
          
          return (
            <p
              key={index}
              className={`text-xl mb-2 ${msg.sender === 'user' ? 'text-user' : 'text-demon'} ${
                (effects.blood || effects.glitch) ? 'demon-effect' : ''
              }`}
              style={messageStyle}
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
          className="flex-1 text-xl p-2 border focus:outline-none"
          placeholder="Введи сообщение..."
          disabled={isDisconnected}
          style={{ color: '#00ff00', borderColor: '#00ff00' }}
        />
        <button
          type="submit"
          className="text-xl border px-4 py-2"
          disabled={isDisconnected}
          style={{ color: '#00ff00', borderColor: '#00ff00' }}
        >
          Отправить
        </button>
      </form>
    </div>
  );
};

ReactDOM.render(<App />, document.getElementById('root'));
