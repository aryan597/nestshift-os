import { useState, useEffect } from 'react';
import nestshiftApi from '../services/nestshiftApi';

const useSystemReady = () => {
  const [nestshiftReady, setNestshiftReady] = useState(false);
  const [haReady, setHaReady] = useState(false);

  useEffect(() => {
    const checkNestshift = async () => {
      try {
        const health = await nestshiftApi.getHealth();
        setNestshiftReady(health.status === 'ok');
      } catch (err) {
        setNestshiftReady(false);
      }
    };

    const checkHA = async () => {
      try {
        const response = await fetch('http://localhost:8123/api/');
        setHaReady(response.ok);
      } catch (err) {
        setHaReady(false);
      }
    };

    // Initial checks
    checkNestshift();
    checkHA();

    // Polling
    const nestshiftInterval = setInterval(checkNestshift, 2000);
    const haInterval = setInterval(checkHA, 3000);

    return () => {
      clearInterval(nestshiftInterval);
      clearInterval(haInterval);
    };
  }, []);

  return {
    nestshiftReady,
    haReady,
    allReady: nestshiftReady && haReady,
  };
};

export default useSystemReady;