import { FileNode, ProjectStats } from '../types';

export const parseFileList = (raw: string): FileNode => {
  const root: FileNode = { name: 'root', path: '.', type: 'directory', children: [] };
  
  // Filter for lines starting with ./ to avoid terminal garbage or empty lines
  const lines = raw.trim().split('\n')
    .map(line => line.trim())
    .filter(line => line.startsWith('./') && line !== './');

  lines.forEach(line => {
    // clean path
    const path = line.replace(/^\.\//, '');
    const parts = path.split('/');
    
    let current = root;
    
    parts.forEach((part, index) => {
      const isFile = index === parts.length - 1;
      let child = current.children?.find(c => c.name === part);

      if (!child) {
        child = {
          name: part,
          path: parts.slice(0, index + 1).join('/'),
          type: isFile ? 'file' : 'directory',
          children: isFile ? undefined : [],
          extension: isFile ? part.split('.').pop() : undefined
        };
        current.children?.push(child);
        // Sort children: directories first, then files
        current.children?.sort((a, b) => {
          if (a.type === b.type) return a.name.localeCompare(b.name);
          return a.type === 'directory' ? -1 : 1;
        });
      }
      current = child;
    });
  });

  return root;
};

export const calculateStats = (root: FileNode): ProjectStats => {
  const stats: ProjectStats = {
    totalFiles: 0,
    totalDirectories: 0,
    extensions: {},
    topDirectories: {}
  };

  const traverse = (node: FileNode) => {
    if (node.type === 'file') {
      stats.totalFiles++;
      const ext = node.extension ? `.${node.extension}` : 'no-ext';
      stats.extensions[ext] = (stats.extensions[ext] || 0) + 1;
    } else {
      if (node.name !== 'root') {
         stats.totalDirectories++;
         // Count direct children of root as top directories
         if (node.path.split('/').length === 1) {
             stats.topDirectories[node.name] = (stats.topDirectories[node.name] || 0) + 1; // Just marking existence
         }
      }
      node.children?.forEach(traverse);
    }
  };

  traverse(root);
  return stats;
};

// Helper to count files strictly inside a top-level dir
export const getFilesPerTopLevelDir = (root: FileNode): {name: string, value: number}[] => {
    const result: {name: string, value: number}[] = [];
    
    root.children?.forEach(child => {
        let count = 0;
        const countFiles = (n: FileNode) => {
            if (n.type === 'file') count++;
            n.children?.forEach(countFiles);
        };
        countFiles(child);
        if (count > 0) {
            result.push({ name: child.name, value: count });
        }
    });
    
    return result.sort((a, b) => b.value - a.value);
};