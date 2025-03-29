import { useQuery } from 'react-query';
import { auth } from '../services/auth';

export function useRole() {
  return useQuery('userRole', auth.getRole, {
    staleTime: 5 * 60 * 1000, // 5 minutes
    cacheTime: 10 * 60 * 1000, // 10 minutes
  });
}