import { createContext, useContext, useEffect, useState } from 'react';

const ModeContext = createContext({
  mode: 'sim',
  profit: false,
  blockchainReady: false,
  marketReady: false
});

export const ModeProvider = ({ children }) => {
  const [modeData, setModeData] = useState({ mode: 'sim', profit: false, blockchainReady: false, marketReady: false });

  useEffect(() => {
    fetch('/mode/status')
      .then(res => res.json())
      .then(data => setModeData(data))
      .catch(err => console.warn('Failed to fetch mode status:', err));
  }, []);

  return <ModeContext.Provider value={modeData}>{children}</ModeContext.Provider>;
};

export const useMode = () => useContext(ModeContext);
