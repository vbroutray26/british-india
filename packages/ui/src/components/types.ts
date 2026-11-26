// Shared component types. Data shapes mirror packages/schema where they overlap.
export interface Column<Row> {
  key: keyof Row & string;
  label: string;
  numeric?: boolean;
  format?: (v: unknown, row: Row) => string;
}
export interface ToastItem { id: string; text: string; tone?: 'info' | 'success' | 'danger' }
export type ReviewStatus = 'accepted' | 'edited' | 'unreviewed' | 'rejected';
export type Lang = 'en' | 'or' | 'hi';
export interface SearchOption { id: string; name: string; matched?: string; type: string; district?: string; href: string }
/** One census figure (spec §7.3 CensusRecord, flattened for charts). */
export interface CensusPoint {
  year: number;
  value: number;
  /** Unit as recorded, e.g. "Puri district (1901 boundaries)". */
  unit: string;
  /** Points are only joined when they share a boundary version (FR-TIME-04). */
  boundary: string;
  approximate?: boolean;
  source: string;
}
export interface GalleryItem {
  id: string; thumb: string; full: string; width: number; height: number;
  alt: string; caption?: string; date?: string; credit: string; sourceHref: string;
}
