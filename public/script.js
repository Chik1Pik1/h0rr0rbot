const { useState, useEffect, useRef } = React;

// Audio context для управления звуком
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

const AudioProvider = ({ children }) => {
  const [signalAudio, setSignalAudio] = useState(null);
  const [backgroundAudio, setBackgroundAudio] = useState(null);
  const [clockAudio, setClockAudio] = useState(null);

  useEffect(() => {
    const signal = new Audio('/music/signal.mp3');
    const background = new Audio('/music/fon.mp3');
    const clock = new Audio('/music/clock.mp3');
    background.loop = true;
    clock.loop = true;

    setSignalAudio(signal);
    setBackgroundAudio(background);
    setClockAudio(clock);

    return () => {
      signal.pause();
      background.pause();
      clock.pause();
    };
  }, []);

  return (
    <AudioContext.Provider value={{ signalAudio, backgroundAudio, clockAudio }}>
      {children}
    </AudioContext.Provider>
  );
};

const generateDailyKey = () => {
  const now = new Date();
  const year = now.getFullYear();
  const month = now.getMonth() + 1;
  const day = now.getDate();
  const seed = (year * 10000 + month * 100 + day) % DEMON_KEYS.length;
  return DEMON_KEYS[seed];
};

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

const CountdownTimer = ({ targetTime, onComplete }) => {
  const { clockAudio } = React.useContext(AudioContext);
  const [timeLeft, setTimeLeft] = useState(calculateTimeLeft());
  const [isClockPlaying, setIsClockPlaying] = useState(false);

  function calculateTimeLeft() {
    const now = new Date();
    const target = targetTime instanceof Date ? targetTime : new Date(targetTime);
    const difference = target - now;

    if (difference <= 0) {
      onComplete();
      return { hours: 0, minutes: 0, seconds: 0 };
    }

    return {
      hours: Math.floor((difference / (1000 * 60 * 60)) % 24),
      minutes: Math.floor((difference / (1000 * 60)) % 60),
      seconds: Math.floor((difference / 1000) % 60)
    };
  }

  useEffect(() => {
    const timer = setInterval(() => {
      const newTime = calculateTimeLeft();
      setTimeLeft(newTime);

      if (newTime.hours + newTime.minutes + newTime.seconds === 0) {
        onComplete();
        clearInterval(timer);
      }
    }, 1000);

    return () => clearInterval(timer);
  }, [targetTime]);

  useEffect(() => {
    if (clockAudio) {
      clockAudio.play().catch(e => console.log('Error playing clock:', e));
      setIsClockPlaying(true);
      
      return () => {
        clockAudio.pause();
        clockAudio.currentTime = 0;
        setIsClockPlaying(false);
      };
    }
  }, [clockAudio]);

  const toggleClockSound = () => {
    if (isClockPlaying) {
      clockAudio.pause();
      setIsClockPlaying(false);
    } else {
      clockAudio.play().catch(e => console.log('Error playing clock:', e));
      setIsClockPlaying(true);
    }
  };

  const drips = Array.from({ length: 20 }).map((_, i) => (
    <div 
      key={i}
      className="blood-drip"
      style={{
        left: `${Math.random() * 100}%`,
        animationDelay: `${Math.random() * 2}s`
      }}
    />
  ));

  return (
    <div className="timer-container">
      <div className="blood-timer">
        {drips}
        {`${timeLeft.hours.toString().padStart(2, '0')}:${timeLeft.minutes.toString().padStart(2, '0')}:${timeLeft.seconds.toString().padStart(2, '0')}`}
      </div>
      <div className="access-status">
        СТАТУС ДОСТУПА: ЗАКРЫТО
      </div>
      <button 
        className="clock-sound-button"
        onClick={toggleClockSound}
      >
        <svg viewBox="0 0 24 24" width="16" height="16">
          <path fill="currentColor" d={isClockPlaying ? 
            "M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02z" :
            "M3 9v6h4l5 5V4L7 9H3z M16.5 12c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02z"}
          />
        </svg>
        {isClockPlaying ? 'Выключить звук часов' : 'Включить звук часов'}
      </button>
    </div>
  );
};

const App = () => {
  const [isAccessGranted, setIsAccessGranted] = useState(false);
  const [showHeadphoneNotification, setShowHeadphoneNotification] = useState(true);

  useEffect(() => {
    if (showHeadphoneNotification) {
      setTimeout(() => {
        setShowHeadphoneNotification(false);
      }, 4000);
    }
  }, []);

  return (
    <AudioProvider>
      <div className="root-container">
        {showHeadphoneNotification && (
          <div className="headphone-notification">
            <div className="headphone-icon">🎧</div>
            <div>Для лучшего эффекта наденьте наушники</div>
          </div>
        )}
        {isAccessGranted ? (
          <ChatScreen />
        ) : (
          <AccessScreen onAccessGranted={() => setIsAccessGranted(true)} />
        )}
      </div>
    </AudioProvider>
  );
};

const AccessScreen = ({ onAccessGranted }) => {
  const { signalAudio } = React.useContext(AudioContext);
  const [key, setKey] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showErrorOverlay, setShowErrorOverlay] = useState(false);
  const [showHackOverlay, setShowHackOverlay] = useState(false);
  const [attemptsLeft, setAttempts] = useState(getAttemptsLeft());
  const [isAccessTime, setIsAccessTime] = useState(false);
  const [blockedUntil, setBlockedUntilState] = useState(getBlockedUntil());

  const checkAccessTime = () => {
    const now = new Date();
    return now.getHours() === 0; // 00:00 - 01:00
  };

  const calculateNextAccessTime = () => {
    const now = new Date();
    const nextAccess = new Date(now);
    
    if (now.getHours() >= 1) {
      nextAccess.setDate(now.getDate() + 1);
    }
    nextAccess.setHours(0, 0, 0, 0);
    
    return nextAccess;
  };

  const checkUserBlock = async (userId) => {
    try {
      const { data, error } = await supabase
        .table('access_blocks')
        .select('blocked_until')
        .eq('user_id', userId)
        .order('created_at', { ascending: false })
        .limit(1)
        .single();

      if (error) throw error;

      if (data) {
        const blockDate = new Date(data.blocked_until);
        if (blockDate > new Date()) {
          setError(`ДОСТУП ЗАБЛОКИРОВАН.\nПОВТОРИТЕ ПОПЫТКУ ПОСЛЕ: ${formatDateTime(blockDate)}`);
          setAttempts(0);
          return true;
        }
      }
      return false;
    } catch (error) {
      console.error('Error checking user block:', error);
      return false;
    }
  };

  const setUserBlock = async (userId) => {
    const blockUntil = new Date(Date.now() + 24 * 60 * 60 * 1000);
    try {
      const { error } = await supabase
        .table('access_blocks')
        .insert({
          user_id: userId,
          blocked_until: blockUntil.toISOString()
        });

      if (error) throw error;

      setError(`ДОСТУП ЗАБЛОКИРОВАН.\nПОВТОРИТЕ ПОПЫТКУ ПОСЛЕ: ${formatDateTime(blockUntil)}`);
      setAttempts(0);
      setBlockedUntilState(blockUntil.toISOString());
      setAttemptsLeft(0);
    } catch (error) {
      console.error('Error setting user block:', error);
      setError('СИСТЕМНАЯ ОШИБКА: ПОПРОБУЙТЕ ПОЗЖЕ');
    }
  };

  useEffect(() => {
    const userId = getUserId();
    checkUserBlock(userId);
    setIsAccessTime(checkAccessTime());

    const interval = setInterval(() => {
      setIsAccessTime(checkAccessTime());
      setBlockedUntilState(getBlockedUntil());
      setAttempts(getAttemptsLeft());
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (!blockedUntil && isAccessTime && attemptsLeft <= 0) {
      setAttempts(3);
      setAttemptsLeft(3);
    }
  }, [blockedUntil, isAccessTime, attemptsLeft]);

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

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!key.trim() || attemptsLeft <= 0) return;

    const userId = getUserId();
    const isBlocked = await checkUserBlock(userId);
    if (isBlocked) return;

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
      setBlockedUntilState(null);

      setTimeout(() => {
        setShowErrorOverlay(false);
        if (signalAudio) {
          signalAudio.pause();
        }
        setShowHackOverlay(true);
        setTimeout(() => {
          setShowHackOverlay(false);
          setError('КЛЮЧ ПРИНЯТ.\nАКТИВИРОВАН ПРОТОКОЛ «ГОРДЕЕВ»...\n\nСИСТЕМА ЗАГРУЖАЕТ РЕЗЕРВНЫЙ КАНАЛ.');
          setTimeout(() => onAccessGranted(), 2000);
        }, 4000);
      }, 3000);
    } else {
      const newAttempts = attemptsLeft - 1;
      setAttempts(newAttempts);
      setAttemptsLeft(newAttempts);
      
      if (newAttempts <= 0) {
        await setUserBlock(userId);
      } else {
        setError(`НЕВЕРНЫЙ КЛЮЧ. ОСТАЛОСЬ ПОПЫТОК: ${newAttempts}`);
      }
      setIsLoading(false);
    }
  };

  const renderTimers = () => {
    if (blockedUntil) {
      const blockedDate = new Date(blockedUntil);
      return (
        <div className="blocked-timer blink">
          <p>ДОСТУП ВОССТАНОВИТСЯ ЧЕРЕЗ:</p>
          <CountdownTimer 
            targetTime={blockedDate}
            onComplete={() => {
              localStorage.removeItem('blockedUntil');
              setAttempts(3);
              setAttemptsLeft(3);
              setBlockedUntilState(null);
            }}
          />
        </div>
      );
    }

    if (!checkAccessTime()) {
      return (
        <div className="text-center">
          <p className="text-demon mb-4">ДОСТУП ОТКРОЕТСЯ ЧЕРЕЗ:</p>
          <CountdownTimer 
            targetTime={calculateNextAccessTime()}
            onComplete={() => setIsAccessTime(true)}
          />
        </div>
      );
    }

    return null;
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
          
          {renderTimers()}

          {!blockedUntil && isAccessTime && attemptsLeft > 0 && (
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
          )}
          {error && (
            <p className="text-demon text-xl mt-4 blink" style={{ whiteSpace: 'pre-line' }}>
              {error}
            </p>
          )}
          {attemptsLeft <= 0 && !blockedUntil && !isAccessTime && (
            <p className="text-demon text-xl blink">ДОСТУП ЗАБЛОКИРОВАН</p>
          )}
        </div>
      </div>
    </>
  );
};

const ChatScreen = () => {
  const { backgroundAudio } = React.useContext(AudioContext);
  const [messages, setMessages] = useState([
    { sender: 'demon', text: 'Теперь я знаю кто ты! Я вижу тебя... через твою камеру).' }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isDisconnected, setIsDisconnected] = useState(false);
  const [isAudioPlaying, setIsAudioPlaying] = useState(false);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const inactivityTimer = useRef(null);
  const [globalEffects, setGlobalEffects] = useState(false);
  const userId = getUserId();
  const [effects, setEffects] = useState({ 
    blood: false, 
    glitch: false 
  });

  const startFearTimer = () => {
    resetFearTimer();
    inactivityTimer.current = setTimeout(() => {
      setMessages(prev => [...prev, { 
        sender: 'demon', 
        text: 'Тишина... Ты испугался? Чего затих вдруг?' 
      }]);
      triggerGlobalEffects();
    }, 300000); // 5 минут
  };

  const resetFearTimer = () => {
    if (inactivityTimer.current) clearTimeout(inactivityTimer.current);
  };

  const triggerGlobalEffects = () => {
    setGlobalEffects(true);
    setTimeout(() => setGlobalEffects(false), 3000);
  };

  useEffect(() => {
    const handleActivity = () => {
      resetFearTimer();
      startFearTimer();
    };

    window.addEventListener('mousemove', handleActivity);
    window.addEventListener('keypress', handleActivity);
    startFearTimer();

    return () => {
      window.removeEventListener('mousemove', handleActivity);
      window.removeEventListener('keypress', handleActivity);
      resetFearTimer();
    };
  }, []);

  useEffect(() => {
    if (backgroundAudio) {
      backgroundAudio.volume = 0.3;
      const playAudio = async () => {
        try {
          await backgroundAudio.play();
          setIsAudioPlaying(true);
        } catch (error) {
          console.log("Autoplay prevented:", error);
          setIsAudioPlaying(false);
        }
      };
      playAudio();
    }
    return () => {
      if (backgroundAudio) {
        backgroundAudio.pause();
        setIsAudioPlaying(false);
      }
    };
  }, [backgroundAudio]);

  const toggleAudio = async () => {
    if (backgroundAudio) {
      try {
        if (isAudioPlaying) {
          backgroundAudio.pause();
          setIsAudioPlaying(false);
        } else {
          await backgroundAudio.play();
          setIsAudioPlaying(true);
        }
      } catch (error) {
        console.log("Audio toggle failed:", error);
      }
    }
  };

  const toggleFullscreen = () => {
    if (window.Telegram?.WebApp) {
      window.Telegram.WebApp.expand();
    } else {
      if (document.fullscreenElement) {
        document.exitFullscreen();
      } else {
        document.documentElement.requestFullscreen().catch(console.error);
      }
    }
  };

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
    <div className={`flex flex-col h-full p-4 relative chat-fullscreen ${globalEffects ? 'global-noise' : ''}`}>
      <div 
        id="chat-container" 
        className={`chat-container ${isDisconnected ? 'chat-disabled' : ''}`}
      >
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

      <div className={`chat-bottom-panel ${isDrawerOpen ? 'drawer-open' : ''}`}>
        <form onSubmit={handleSubmit} className="chat-input-form">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            className="flex-1 text-xl p-2 border focus:outline-none"
            placeholder="Напиши мне..."
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

        <div className="drawer-container">
          <div 
            className="drawer-handle"
            onClick={() => setIsDrawerOpen(!isDrawerOpen)}
            style={{
              transform: isDrawerOpen ? 'rotate(180deg)' : 'rotate(0deg)'
            }}
          />
          
          <div 
            className="drawer-content"
            style={{
              height: isDrawerOpen ? '60px' : '0'
            }}
          >
            <div className="drawer-buttons">
              <button
                onClick={toggleAudio}
                className="control-button"
                disabled={!backgroundAudio}
                style={{
                  background: 'none',
                  border: '1px solid #00ff00',
                  color: '#00ff00',
                  padding: '8px 16px',
                  borderRadius: '4px',
                  cursor: backgroundAudio ? 'pointer' : 'not-allowed',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  opacity: backgroundAudio ? 1 : 0.5
                }}
              >
                <svg viewBox="0 0 24 24">
                  {isAudioPlaying ? (
                    <path d="M14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77 0-4.28-2.99-7.86-7-8.77zm-4 0l-4 4-4-4-3 3 4 4-4 4 3 3 4-4 4 4 3-3-4-4 4-4-3-3-4 4zM12 7v10l-3.2-3.2-2.8 2.8-2-2 2.8-2.8-2.8-2.8 2-2 2.8 2.8 3.2-3.2z"/>
                  ) : (
                    <path d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51c.66-1.24 1.03-2.65 1.03-4.15s-.37-2.91-1.03-4.15l-1.51 1.51c.34.82.54 1.7.54 2.64zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z"/>
                  )}
                </svg>
                Звук
              </button>
              
              <button
                onClick={toggleFullscreen}
                className="control-button"
                style={{
                  background: 'none',
                  border: '1px solid #00ff00',
                  color: '#00ff00',
                  padding: '8px 16px',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}
              >
                <svg viewBox="0 0 24 24">
                  <path d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"/>
                </svg>
                Полный экран
              </button>
            </div>
          </div>
        </div>
      </div>

      {globalEffects && (
        <div className="global-distortion-overlay">
          <div className="noise-texture"/>
          <div className="scanlines"/>
        </div>
      )}
    </div>
  );
};

ReactDOM.render(<App />, document.getElementById('root'));
