// ARQUIVO: src/types/odontograma.ts

// 1. Exporta as faces (Note o 'export' na frente)
export type ToothFace = 'vestibular' | 'lingual' | 'distal' | 'mesial' | 'oclusal' | 'occlusal';

// 2. Exporta os tipos de tratamento
export type TreatmentType = 'caries' | 'restoration' | 'canal' | 'extraction' | 'implant' | null;

// 3. Exporta o estado do dente (ESTA É A PARTE QUE O ERRO DIZ QUE FALTA)
export interface ToothState {
  [key: string]: TreatmentType;
}

// 4. Exporta configuração visual
export interface ToolConfig {
  label: string;
  color: string;
  cursor: string;
}