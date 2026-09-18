export type Language = 'en' | 'pa' | 'hi';

export interface AgentCardData {
  id: string;
  name: string;
  badge: 'High' | 'Standby' | 'Processing' | 'Completed';
  badgeColor: string;
  description: string;
  status: 'Completed' | 'Processing' | 'Idle' | 'Active';
  timestamp: string;
  input: string;
  output: string;
  details: { label: string; value: string; highlight?: boolean }[];
  isActive?: boolean;
}

export interface EventLog {
  id: string;
  timestamp: string;
  agent: 'Executor' | 'Strategist' | 'Sentinel';
  eventType: string;
  message: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
}

export interface RiskNode {
  id: string;
  name: string;
  district: string;
  threatLevel: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  waterLevelPct: number;
  precipRate: string;
  population: string;
  evacStatus: 'MANDATORY' | 'ADVISORY' | 'STANDBY' | 'SAFE';
  mitigation: string;
  coords: [number, number]; // [lat, lng]
}

export interface EmergencyActionItem {
  id: string;
  stepNumber: string;
  title: string;
  deadline: string;
  status: 'In Progress' | 'Pending' | 'Completed';
}

export interface FarmActionItem {
  id: string;
  stepNumber: string;
  title: string;
  deadline: string;
  status: 'In Progress' | 'Pending' | 'Completed';
}

export interface RiskFactorItem {
  id: string;
  name: string;
  severity: 'HIGH' | 'MEDIUM' | 'LOW';
  confidence: number;
  description: string;
}

export type NavigationTab = 'citizen' | 'command' | 'risk' | 'emergency' | 'agriculture' | 'weathergpt';

export type UserRole = 'OFFICER' | 'SCIENTIST' | 'CITIZEN';

export interface UserProfile {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  designation: string;
  organization: string;
  badgeNumber?: string;
  district: string;
  phone?: string;
}

