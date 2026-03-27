export interface SimParams {
  seed: number;
  num_epochs: number;
  mutation_rate: number;
  grid_width: number;
  grid_height: number;
  replicator_threshold: number;
}

export type ClientMessage =
  | { type: 'start'; params: SimParams }
  | { type: 'pause' }
  | { type: 'resume' }
  | { type: 'stop' }
  | { type: 'step'; count: number }
  | { type: 'set_mutation_rate'; value: number };

export interface MetricsMessage {
  type: 'metrics';
  epoch: number;
  opcode_percent: number;
  shannon_entropy: number;
}

export interface StatusMessage {
  type: 'status';
  state: 'running' | 'paused' | 'warming_up' | 'completed' | 'stopped';
}

export interface ReplicatorMessage {
  type: 'replicator';
  epoch: number;
}

export interface ConfigMessage {
  type: 'config';
  grid_width: number;
  grid_height: number;
  num_epochs: number;
}

export interface ErrorMessage {
  type: 'error';
  message: string;
}

export type ServerMessage = MetricsMessage | StatusMessage | ReplicatorMessage | ConfigMessage | ErrorMessage;

export interface MetricsPoint {
  epoch: number;
  opcode_percent: number;
  shannon_entropy: number;
}
