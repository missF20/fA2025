import { useEffect, useRef, useState, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';
import { config } from '../config';
import { log } from '../utils/logger';

interface UseSocketOptions {
  autoConnect?: boolean;
  reconnectionAttempts?: number;
  reconnectionDelay?: number;
}

export function useSocket(options: UseSocketOptions = {}) {
  const {
    autoConnect = true,
    reconnectionAttempts = 5,
    reconnectionDelay = 5000,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const socketRef = useRef<Socket | null>(null);
  const reconnectAttemptsRef = useRef(0);

  const connect = useCallback(() => {
    if (socketRef.current?.connected) return;

    socketRef.current = io(config.api.socketUrl, {
      autoConnect: false,
      reconnection: false,
      transports: ['websocket'],
    });

    socketRef.current.on('connect', () => {
      setIsConnected(true);
      setError(null);
      reconnectAttemptsRef.current = 0;
      log.info('Socket connected');
    });

    socketRef.current.on('disconnect', (reason) => {
      setIsConnected(false);
      log.warn('Socket disconnected:', { reason });

      if (reconnectAttemptsRef.current < reconnectionAttempts) {
        setTimeout(() => {
          reconnectAttemptsRef.current++;
          connect();
        }, reconnectionDelay);
      } else {
        setError(new Error('Maximum reconnection attempts reached'));
      }
    });

    socketRef.current.on('connect_error', (error) => {
      log.error('Socket connection error:', error);
      setError(error);
    });

    socketRef.current.connect();

    return () => {
      socketRef.current?.disconnect();
      socketRef.current = null;
    };
  }, [reconnectionAttempts, reconnectionDelay]);

  useEffect(() => {
    if (autoConnect) {
      connect();
    }
    return () => {
      socketRef.current?.disconnect();
    };
  }, [autoConnect, connect]);

  const emit = useCallback((event: string, data: any) => {
    if (!socketRef.current?.connected) {
      throw new Error('Socket not connected');
    }
    socketRef.current.emit(event, data);
  }, []);

  const on = useCallback((event: string, callback: (data: any) => void) => {
    if (!socketRef.current) {
      throw new Error('Socket not initialized');
    }
    socketRef.current.on(event, callback);
    return () => {
      socketRef.current?.off(event, callback);
    };
  }, []);

  return {
    isConnected,
    error,
    connect,
    emit,
    on,
  };
}