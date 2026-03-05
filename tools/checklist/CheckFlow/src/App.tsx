import { useState } from 'react';
import Landing from './pages/Landing';
import SAMUI from './pages/SAMUI';

interface UserSession {
  username: string;
  role: 'Admin' | 'User';
}

export default function App() {
  const [session, setSession] = useState<UserSession | null>(null);

  if (!session) {
    return <Landing onStart={(user: UserSession) => setSession(user)} />;
  }

  return <SAMUI actorName={session.username} role={session.role} />;
}
