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
    setIsLoading(true);
    setError('Проверка ключа...');
    setTimeout(() => {
      setShowErrorOverlay(true); // Показать анимацию ошибки
      setTimeout(() => {
        setShowErrorOverlay(false);
        setShowHackOverlay(true); // Показать анимацию взлома
        setTimeout(() => {
          setShowHackOverlay(false);
          setError('ОШИБКА: КЛЮЧ НЕВЕРЕН.\nАКТИВИРОВАН ПРОТОКОЛ «ГОРДЕЕВ»...\n\nWARNING: СИСТЕМА ЗАГРУЖАЕТ РЕЗЕРВНЫЙ КАНАЛ.\nПОДКЛЮЧЕНИЕ К СУЩНОСТИ #7... УСПЕШНО.');
          setTimeout(() => onAccessGranted(), 2000);
        }, 3000); // Длительность анимации взлома
      }, 3000); // Длительность анимации ошибки
    }, 3000); // Задержка перед анимацией
  };

  // Генерация случайных кусков кода для анимации взлома
  const generateHackCode = () => {
    const snippets = [
      '0x7F3A 48B2 MOV AX, [BX]',
      'jmp 0xFF34; hack.init()',
      'sudo rm -rf /system',
      'while(1) { exploit() }',
      '#define HACK 0xDEADBEEF',
      '10101010 11110000',
      'sys_call: int 0x80',
      'ptr = *(0xCAFEBABE)',
      'exec("backdoor")',
      'for(i=0;i<0xFF;i++)'
    ];
    const codes = [];
    for (let i = 0; i < 20; i++) {
      const top = Math.random() * 100;
      const left = Math.random() * 100;
      const duration = 0.5 + Math.random() * 0.5; // Ускоряем: 0.5–1 секунда
      codes.push(
        <div
          key={i}
          className="hack-code"
          style={{
            top: `${top}%`,
            left: `${left}%`,
            animationDuration: `${duration}s`
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
      {error ? (
        <p className="text-demon text-xl mt-4 blink" style={{ whiteSpace: 'pre-line' }}>{error}</p>
      ) : (
        <p className="text-demon text-xl mt-4">(ЛЮБОЙ ВВОД → ОШИБКА)</p>
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
            className={`text-xl mb-2 ${msg.sender === 'user' ? 'text-user' : 'text-demon'}`}
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
