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
        }, 4000); // Увеличена длительность анимации взлома
      }, 3000);
    }, 3000);
  };

  // Новая анимация взлома
  const generateHackCode = () => {
    const snippets = [
      'INITIALIZE BACKDOOR: 0xDEADBEEF',
      'BYPASS FIREWALL: EXEC 0xFF',
      'INJECT PAYLOAD: SYS_CALL 0x80',
      'OVERRIDE: 10101010 11110000',
      'ROOTKIT DEPLOY: ptr=0xCAFEBABE',
      'CRYPTO BREACH: AES-256 CRACK',
      'SHADOW PROTOCOL: jmp 0xFF34',
      'GHOST THREAD: fork() EXPLOIT'
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
            onChange={(e) => setKey██

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
