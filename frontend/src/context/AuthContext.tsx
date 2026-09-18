import React, { createContext, useContext, useState, useEffect } from 'react';
import { UserProfile, UserRole } from '../types';

interface AuthContextType {
  user: UserProfile | null;
  isAuthenticated: boolean;
  login: (profile: Partial<UserProfile> & { role: UserRole }) => void;
  logout: () => void;
  isLoginModalOpen: boolean;
  setIsLoginModalOpen: (open: boolean) => void;
}

const DEFAULT_USER: UserProfile = {
  id: 'usr_deoc_patiala_01',
  name: 'Gurinder Singh Sandhu',
  email: 'deoc.patiala@punjab.gov.in',
  role: 'OFFICER',
  designation: 'District Emergency Operations Officer',
  organization: 'Punjab State Disaster Management Authority (PSDMA)',
  badgeNumber: 'PB-DEOC-409',
  district: 'Patiala, Punjab',
  phone: '+91 98765-43210',
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(() => {
    try {
      const saved = localStorage.getItem('weathergpt_user_session');
      if (saved) {
        return JSON.parse(saved);
      }
    } catch (e) {
      console.warn('Failed to parse auth session', e);
    }
    return null; // Prompt login like ChatGPT or Gemini in the starting
  });

  const [isLoginModalOpen, setIsLoginModalOpen] = useState<boolean>(false);

  const login = (profile: Partial<UserProfile> & { role: UserRole }) => {
    let completeProfile: UserProfile;

    if (profile.role === 'OFFICER') {
      completeProfile = {
        id: profile.id || 'usr_deoc_01',
        name: profile.name || 'Harpreet Singh Brar',
        email: profile.email || 'officer.patiala@punjab.gov.in',
        role: 'OFFICER',
        designation: profile.designation || 'District Emergency Operations Officer',
        organization: profile.organization || 'Punjab State Disaster Management Authority (PSDMA)',
        badgeNumber: profile.badgeNumber || 'PB-DEOC-409',
        district: profile.district || 'Patiala, Punjab',
        phone: profile.phone || '+91 98765-43210',
      };
    } else if (profile.role === 'SCIENTIST') {
      completeProfile = {
        id: profile.id || 'usr_pau_02',
        name: profile.name || 'Dr. Manjit Kaur Gill',
        email: profile.email || 'agromet.scientist@pau.edu',
        role: 'SCIENTIST',
        designation: profile.designation || 'Senior Agro-Meteorologist & Extension Specialist',
        organization: profile.organization || 'Punjab Agricultural University (PAU), Ludhiana',
        badgeNumber: profile.badgeNumber || 'PAU-SCI-118',
        district: profile.district || 'Ludhiana Central',
        phone: profile.phone || '+91 98140-55443',
      };
    } else {
      completeProfile = {
        id: profile.id || 'usr_cit_03',
        name: profile.name || 'Jagtar Singh Dhillon',
        email: profile.email || 'jagtar.farmer@gmail.com',
        role: 'CITIZEN',
        designation: profile.designation || 'Farmer / Resident (Wards 12-14)',
        organization: profile.organization || 'Citizen Portal (Patiala Rural)',
        district: profile.district || 'Patiala, Punjab',
        phone: profile.phone || '+91 94172-88776',
      };
    }

    setUser(completeProfile);
    localStorage.setItem('weathergpt_user_session', JSON.stringify(completeProfile));
    setIsLoginModalOpen(false);
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('weathergpt_user_session');
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: Boolean(user),
        login,
        logout,
        isLoginModalOpen,
        setIsLoginModalOpen,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
