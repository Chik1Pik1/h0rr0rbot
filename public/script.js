const { useState, useEffect } = React;

const App = () => {
  const [isAccessGranted, setIsAccessGranted] = useState(false);

  return (
    <div className="crt-window">
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

  const handleSubmit = (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('Проверка ключа...');
    setTimeout(() => {
      setError('ОШИБКА: Неверный ключ доступа');
      setTimeout(() => {
        setError('Доступ разрешен. Сущность #3 активирована.');
        setTimeout(() => onAccessGranted(), 2000);
      }, 3000);
    }, 2000);
  };

  return (
    <div className="flex flex-col items-center justify-center h-full text-center">
      <h1 className="text- Stad3xl text-demon mb-4">ПРОЕКТ ЗЕРКАЛО-1</h1>
      <p className="text-xl text-demon mb-4">ГРИФ: СОВЕРШЕННО СЕКРЕТНО</p>
      <form onSubmit={handleSubmit} className="w-full max-w-sm">
        <input
          type="text"
          value={key}
          onChange={(e) => setKey(e.target.value)}
          className="w-full text-user text-xl p-2 mb-4 border focus:outline-none"
          placeholder="Введите ключ доступа"
          disabled={isLoading}
        />
        <button
          type="submit"
          className="w-full text-user text-xl border px-4 py-2"
          disabled={isLoading}
        >
          Подтвердить
        </button>
      </form>
      {error && (
        <p className="text-demon text-xl mt-4 blink">{error}</p>
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
    <div className="flex flex-col h-full p-4">
      <div className="chat-container">
        {messages.map((msg, index) => (
          <p
            key={index}
            className={`text-xl mb-2 ${msg.sender === 'user' ? 'text-user' : 'text-demon'}`}
          >
            {msg.sender === 'user' ? '>> ' : '[Сущность #3]: '}{msg.text}
          </p>
        ))}
        {isTyping && (
          <p className="text-demon text-xl blink">[Сущность #3]: ...печатает...</p>
        )}
      </div>
      <form onSubmit={handleSubmit} className="flex mt-auto w-full">
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
