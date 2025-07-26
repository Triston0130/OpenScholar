/**
 * Collection Backup and Recovery System
 * Ensures collections are never lost
 */

import { Collection, SavedPaper, Folder, CollectionWithPapers } from './collections';

const COLLECTIONS_KEY = 'openscholar_collections';
const BACKUP_KEY_PREFIX = 'openscholar_collections_backup_';
const MAX_BACKUPS = 5;

interface BackupMetadata {
  timestamp: string;
  version: string;
  totalCollections: number;
  totalPapers: number;
}

interface Backup {
  metadata: BackupMetadata;
  data: any;
}

/**
 * Create a backup of current collections data
 */
export function createBackup(): string {
  try {
    const currentData = localStorage.getItem(COLLECTIONS_KEY);
    if (!currentData) return '';

    const parsedData = JSON.parse(currentData);
    const timestamp = new Date().toISOString();
    const backupKey = `${BACKUP_KEY_PREFIX}${Date.now()}`;

    const backup: Backup = {
      metadata: {
        timestamp,
        version: '1.0',
        totalCollections: parsedData.collections?.length || 0,
        totalPapers: Object.values(parsedData.papers || {}).reduce(
          (sum: number, papers: any) => sum + (Array.isArray(papers) ? papers.length : 0),
          0
        )
      },
      data: parsedData
    };

    // Store backup
    localStorage.setItem(backupKey, JSON.stringify(backup));

    // Clean old backups
    cleanOldBackups();

    return backupKey;
  } catch (error) {
    console.error('Failed to create backup:', error);
    return '';
  }
}

/**
 * Auto-backup collections periodically
 */
export function enableAutoBackup() {
  // Create initial backup
  createBackup();

  // Set up periodic backups (every 30 minutes)
  setInterval(() => {
    createBackup();
  }, 30 * 60 * 1000);

  // Backup on significant events
  window.addEventListener('beforeunload', () => {
    createBackup();
  });

  // Listen for collection changes
  window.addEventListener('collectionsChanged', () => {
    // Debounce to avoid too many backups
    clearTimeout((window as any).backupTimeout);
    (window as any).backupTimeout = setTimeout(() => {
      createBackup();
    }, 5000); // 5 seconds after last change
  });
}

/**
 * List all available backups
 */
export function listBackups(): Array<{ key: string; metadata: BackupMetadata }> {
  const backups: Array<{ key: string; metadata: BackupMetadata }> = [];

  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (key && key.startsWith(BACKUP_KEY_PREFIX)) {
      try {
        const backup = JSON.parse(localStorage.getItem(key) || '{}') as Backup;
        if (backup.metadata) {
          backups.push({ key, metadata: backup.metadata });
        }
      } catch (error) {
        console.error(`Invalid backup ${key}:`, error);
      }
    }
  }

  // Sort by timestamp (newest first)
  return backups.sort((a, b) => 
    new Date(b.metadata.timestamp).getTime() - new Date(a.metadata.timestamp).getTime()
  );
}

/**
 * Restore from a specific backup
 */
export function restoreFromBackup(backupKey: string): boolean {
  try {
    const backupData = localStorage.getItem(backupKey);
    if (!backupData) {
      console.error('Backup not found:', backupKey);
      return false;
    }

    const backup = JSON.parse(backupData) as Backup;
    
    // Create a backup of current data before restoring
    const currentBackupKey = createBackup();
    console.log('Created backup of current data:', currentBackupKey);

    // Restore the backup
    localStorage.setItem(COLLECTIONS_KEY, JSON.stringify(backup.data));

    // Dispatch event to notify components
    window.dispatchEvent(new CustomEvent('collectionsRestored', { 
      detail: { backupKey, timestamp: backup.metadata.timestamp } 
    }));

    return true;
  } catch (error) {
    console.error('Failed to restore backup:', error);
    return false;
  }
}

/**
 * Export collections to a downloadable file
 */
export function exportCollections(format: 'json' | 'readable' = 'json'): void {
  try {
    const data = localStorage.getItem(COLLECTIONS_KEY);
    if (!data) {
      alert('No collections to export');
      return;
    }

    const parsedData = JSON.parse(data);
    let content: string;
    let filename: string;
    let mimeType: string;

    if (format === 'json') {
      // Full JSON export
      const exportData = {
        version: '1.0',
        exportDate: new Date().toISOString(),
        source: 'OpenScholar',
        ...parsedData
      };
      content = JSON.stringify(exportData, null, 2);
      filename = `openscholar_collections_${new Date().toISOString().split('T')[0]}.json`;
      mimeType = 'application/json';
    } else {
      // Human-readable export
      content = generateReadableExport(parsedData);
      filename = `openscholar_collections_${new Date().toISOString().split('T')[0]}.md`;
      mimeType = 'text/markdown';
    }

    // Create and download file
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  } catch (error) {
    console.error('Failed to export collections:', error);
    alert('Failed to export collections');
  }
}

/**
 * Import collections from a file
 */
export function importCollections(file: File): Promise<boolean> {
  return new Promise((resolve) => {
    const reader = new FileReader();
    
    reader.onload = (e) => {
      try {
        const content = e.target?.result as string;
        const importData = JSON.parse(content);
        
        // Validate import data
        if (!importData.collections || !importData.papers) {
          throw new Error('Invalid import file format');
        }

        // Create backup before importing
        const backupKey = createBackup();
        console.log('Created backup before import:', backupKey);

        // Merge or replace (for now, we'll replace)
        localStorage.setItem(COLLECTIONS_KEY, JSON.stringify({
          collections: importData.collections,
          papers: importData.papers,
          folders: importData.folders || {}
        }));

        // Dispatch event
        window.dispatchEvent(new CustomEvent('collectionsImported'));
        
        resolve(true);
      } catch (error) {
        console.error('Failed to import collections:', error);
        alert('Failed to import collections. Please check the file format.');
        resolve(false);
      }
    };

    reader.readAsText(file);
  });
}

/**
 * Clean old backups to save space
 */
function cleanOldBackups(): void {
  const backups = listBackups();
  
  // Keep only the most recent MAX_BACKUPS
  if (backups.length > MAX_BACKUPS) {
    const toDelete = backups.slice(MAX_BACKUPS);
    toDelete.forEach(backup => {
      localStorage.removeItem(backup.key);
    });
  }
}

/**
 * Generate human-readable export
 */
function generateReadableExport(data: any): string {
  const lines: string[] = [];
  
  lines.push('# OpenScholar Collections Export');
  lines.push(`Generated: ${new Date().toLocaleString()}`);
  lines.push('');
  
  // Collections summary
  lines.push('## Collections Summary');
  lines.push(`Total collections: ${data.collections?.length || 0}`);
  lines.push(`Total papers: ${Object.values(data.papers || {}).reduce((sum: number, papers: any) => sum + (Array.isArray(papers) ? papers.length : 0), 0)}`);
  lines.push('');
  
  // Each collection
  data.collections?.forEach((collection: Collection) => {
    lines.push(`## ${collection.name}`);
    if (collection.description) {
      lines.push(`*${collection.description}*`);
    }
    lines.push(`Created: ${new Date(collection.createdAt).toLocaleDateString()}`);
    lines.push('');
    
    const papers = data.papers[collection.id] || [];
    lines.push(`### Papers (${papers.length})`);
    
    papers.forEach((paper: SavedPaper, index: number) => {
      lines.push(`${index + 1}. **${paper.title}** (${paper.year})`);
      lines.push(`   - Authors: ${paper.authors.join(', ')}`);
      if (paper.doi) lines.push(`   - DOI: ${paper.doi}`);
      if (paper.tags && paper.tags.length > 0) {
        lines.push(`   - Tags: ${paper.tags.join(', ')}`);
      }
      lines.push('');
    });
    
    lines.push('---');
    lines.push('');
  });
  
  return lines.join('\n');
}

/**
 * Check if collections exist and are valid
 */
export function validateCollections(): { isValid: boolean; issues: string[] } {
  const issues: string[] = [];
  
  try {
    const data = localStorage.getItem(COLLECTIONS_KEY);
    if (!data) {
      issues.push('No collections data found');
      return { isValid: false, issues };
    }
    
    const parsedData = JSON.parse(data);
    
    // Check structure
    if (!parsedData.collections || !Array.isArray(parsedData.collections)) {
      issues.push('Invalid collections array');
    }
    
    if (!parsedData.papers || typeof parsedData.papers !== 'object') {
      issues.push('Invalid papers object');
    }
    
    // Check for orphaned papers
    const collectionIds = new Set(parsedData.collections?.map((c: Collection) => c.id) || []);
    Object.keys(parsedData.papers || {}).forEach(id => {
      if (!collectionIds.has(id)) {
        issues.push(`Orphaned papers in collection ${id}`);
      }
    });
    
    return { isValid: issues.length === 0, issues };
  } catch (error) {
    issues.push(`Parse error: ${error}`);
    return { isValid: false, issues };
  }
}

/**
 * Initialize backup system
 */
export function initializeBackupSystem(): void {
  // Validate current data
  const validation = validateCollections();
  if (!validation.isValid) {
    console.warn('Collection validation issues:', validation.issues);
  }
  
  // Enable auto-backup
  enableAutoBackup();
  
  // Log backup status
  const backups = listBackups();
  console.log(`Backup system initialized. ${backups.length} backups available.`);
}