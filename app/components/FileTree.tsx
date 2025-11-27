import React, { useState } from 'react';
import { FileNode } from '../types';
import { Folder, FileText, ChevronRight, ChevronDown, FileCode, FileJson, FileType, Database } from 'lucide-react';

interface FileTreeProps {
  node: FileNode;
  level?: number;
}

const getFileIcon = (name: string) => {
  if (name.endsWith('.tsx') || name.endsWith('.ts') || name.endsWith('.js')) return <FileCode className="w-4 h-4 text-blue-400" />;
  if (name.endsWith('.py')) return <FileType className="w-4 h-4 text-yellow-400" />;
  if (name.endsWith('.sol')) return <Database className="w-4 h-4 text-purple-400" />; // Solidity
  if (name.endsWith('.json') || name.endsWith('.yml')) return <FileJson className="w-4 h-4 text-orange-400" />;
  return <FileText className="w-4 h-4 text-slate-500" />;
};

const FileTreeNode: React.FC<FileTreeProps> = ({ node, level = 0 }) => {
  const [isOpen, setIsOpen] = useState(level < 2); // Auto-expand first 2 levels
  const hasChildren = node.type === 'directory' && node.children && node.children.length > 0;

  const toggleOpen = () => setIsOpen(!isOpen);

  // If it's the root node, just render children
  if (node.name === 'root') {
    return (
      <div className="w-full font-mono text-sm">
        {node.children?.map((child) => (
          <FileTreeNode key={child.path} node={child} level={level} />
        ))}
      </div>
    );
  }

  return (
    <div className="select-none">
      <div 
        className={`flex items-center py-1 px-2 hover:bg-slate-800/50 rounded cursor-pointer transition-colors ${level === 0 ? 'mb-1' : ''}`}
        style={{ paddingLeft: `${level * 16 + 8}px` }}
        onClick={toggleOpen}
      >
        <span className="mr-2 opacity-70">
           {node.type === 'directory' ? (
             isOpen ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />
           ) : <span className="w-3 block"></span>}
        </span>
        
        <span className="mr-2">
          {node.type === 'directory' ? (
            <Folder className={`w-4 h-4 ${isOpen ? 'text-cyan-500' : 'text-slate-600'}`} />
          ) : getFileIcon(node.name)}
        </span>
        
        <span className={`${node.type === 'directory' ? 'text-slate-200 font-semibold' : 'text-slate-400'}`}>
          {node.name}
        </span>
      </div>

      {hasChildren && isOpen && (
        <div className="border-l border-slate-800 ml-[15px]">
          {node.children?.map((child) => (
            <FileTreeNode key={child.path} node={child} level={level + 1} />
          ))}
        </div>
      )}
    </div>
  );
};

export default FileTreeNode;