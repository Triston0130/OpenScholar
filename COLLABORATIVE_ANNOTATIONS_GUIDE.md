# Collaborative Annotations Guide

## Overview

The OpenScholar platform now supports collaborative annotations on PDFs within shared collections. Multiple users can:
- Share highlights and comments
- Reply to each other's annotations
- See who made which annotation
- Work together on the same documents

## Backend API Endpoints

### Collection Sharing
- `POST /api/collections/{collection_id}/share` - Share a collection
- `GET /api/collections/{collection_id}/shares` - Get all shares
- `GET /api/collections/{collection_id}/collaborators` - Get all collaborators

### Annotations
- `POST /api/annotations` - Create annotation
- `GET /api/papers/{paper_id}/annotations` - Get annotations (includes shared)
- `PUT /api/annotations/{annotation_id}` - Update annotation
- `DELETE /api/annotations/{annotation_id}` - Delete annotation

### Annotation Replies
- `POST /api/annotations/{annotation_id}/replies` - Add reply
- `GET /api/annotations/{annotation_id}/replies` - Get replies

## Frontend Integration

### 1. Import the annotation sync service

```typescript
import { annotationSync } from '../utils/annotationSync';
```

### 2. Set up authentication

```typescript
// In your auth context or after login
annotationSync.setAuthToken(authToken);
```

### 3. Create a collaborative PDF viewer component

```typescript
import React, { useState, useEffect } from 'react';
import { annotationSync, CollaborativeAnnotation, Collaborator } from '../utils/annotationSync';

interface CollaborativePDFViewerProps {
  paperId: string;
  pdfUrl: string;
  collectionId?: string;
}

export const CollaborativePDFViewer: React.FC<CollaborativePDFViewerProps> = ({
  paperId,
  pdfUrl,
  collectionId
}) => {
  const [annotations, setAnnotations] = useState<CollaborativeAnnotation[]>([]);
  const [collaborators, setCollaborators] = useState<Collaborator[]>([]);
  const [selectedAnnotation, setSelectedAnnotation] = useState<string | null>(null);

  useEffect(() => {
    // Load initial data
    loadAnnotations();
    if (collectionId) {
      loadCollaborators();
    }

    // Start real-time sync
    const cleanup = annotationSync.startSync(
      paperId,
      collectionId,
      (updatedAnnotations) => {
        setAnnotations(updatedAnnotations);
      }
    );

    return cleanup;
  }, [paperId, collectionId]);

  const loadAnnotations = async () => {
    try {
      const data = await annotationSync.getAnnotations(paperId, collectionId);
      setAnnotations(data);
    } catch (error) {
      console.error('Failed to load annotations:', error);
    }
  };

  const loadCollaborators = async () => {
    if (!collectionId) return;
    try {
      const data = await annotationSync.getCollaborators(collectionId);
      setCollaborators(data);
    } catch (error) {
      console.error('Failed to load collaborators:', error);
    }
  };

  const handleTextSelection = async (selection: {
    text: string;
    pageNumber: number;
    position: { x: number; y: number; width: number; height: number };
  }) => {
    try {
      const annotation = await annotationSync.createAnnotation({
        paper_id: paperId,
        collection_id: collectionId,
        annotation_type: 'highlight',
        color: '#FFFF00',
        page_number: selection.pageNumber,
        position_x: selection.position.x,
        position_y: selection.position.y,
        width: selection.position.width,
        height: selection.position.height,
        selected_text: selection.text,
        shared_in_collection: true // Share by default in collections
      });

      setAnnotations([...annotations, annotation]);
    } catch (error) {
      console.error('Failed to create annotation:', error);
    }
  };

  const handleAddComment = async (annotationId: string, comment: string) => {
    try {
      await annotationSync.updateAnnotation(annotationId, { comment });
      loadAnnotations();
    } catch (error) {
      console.error('Failed to add comment:', error);
    }
  };

  const handleToggleSharing = async (annotationId: string, shared: boolean) => {
    try {
      await annotationSync.updateAnnotation(annotationId, {
        shared_in_collection: shared
      });
      loadAnnotations();
    } catch (error) {
      console.error('Failed to toggle sharing:', error);
    }
  };

  return (
    <div className="collaborative-pdf-viewer">
      {/* Collaborators bar */}
      {collaborators.length > 0 && (
        <div className="collaborators-bar">
          <h3>Collaborators ({collaborators.length})</h3>
          <div className="collaborator-list">
            {collaborators.map(collaborator => (
              <div key={collaborator.id} className="collaborator">
                <img 
                  src={collaborator.avatar_url || '/default-avatar.png'} 
                  alt={collaborator.name}
                  className="collaborator-avatar"
                />
                <span>{collaborator.name}</span>
                <span className="role">({collaborator.role})</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* PDF Viewer with annotations */}
      <div className="pdf-container">
        {/* Your existing PDF viewer component */}
        {/* Overlay annotations on the PDF */}
        {annotations.map(annotation => (
          <div
            key={annotation.id}
            className={`annotation-overlay ${annotation.annotation_type}`}
            style={{
              position: 'absolute',
              left: `${annotation.position_x}px`,
              top: `${annotation.position_y}px`,
              width: `${annotation.width}px`,
              height: `${annotation.height}px`,
              backgroundColor: annotation.color + '40', // Semi-transparent
              border: `2px solid ${annotation.color}`,
              cursor: 'pointer'
            }}
            onClick={() => setSelectedAnnotation(annotation.id)}
          >
            {annotation.user_id !== currentUserId && (
              <div className="annotation-author">
                {annotation.user_name}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Annotation details panel */}
      {selectedAnnotation && (
        <AnnotationDetailsPanel
          annotation={annotations.find(a => a.id === selectedAnnotation)!}
          onClose={() => setSelectedAnnotation(null)}
          onAddComment={handleAddComment}
          onToggleSharing={handleToggleSharing}
        />
      )}
    </div>
  );
};
```

### 4. Create an annotation details panel

```typescript
interface AnnotationDetailsPanelProps {
  annotation: CollaborativeAnnotation;
  onClose: () => void;
  onAddComment: (annotationId: string, comment: string) => void;
  onToggleSharing: (annotationId: string, shared: boolean) => void;
}

const AnnotationDetailsPanel: React.FC<AnnotationDetailsPanelProps> = ({
  annotation,
  onClose,
  onAddComment,
  onToggleSharing
}) => {
  const [replies, setReplies] = useState<AnnotationReply[]>([]);
  const [newReply, setNewReply] = useState('');

  useEffect(() => {
    loadReplies();
  }, [annotation.id]);

  const loadReplies = async () => {
    try {
      const data = await annotationSync.getReplies(annotation.id);
      setReplies(data);
    } catch (error) {
      console.error('Failed to load replies:', error);
    }
  };

  const handleAddReply = async () => {
    if (!newReply.trim()) return;

    try {
      await annotationSync.addReply(annotation.id, newReply);
      setNewReply('');
      loadReplies();
    } catch (error) {
      console.error('Failed to add reply:', error);
    }
  };

  return (
    <div className="annotation-details-panel">
      <div className="panel-header">
        <h3>Annotation by {annotation.user_name || 'You'}</h3>
        <button onClick={onClose}>×</button>
      </div>

      <div className="annotation-content">
        <div className="selected-text">
          "{annotation.selected_text}"
        </div>

        {annotation.comment && (
          <div className="annotation-comment">
            <strong>Comment:</strong> {annotation.comment}
          </div>
        )}

        <div className="annotation-actions">
          <label>
            <input
              type="checkbox"
              checked={annotation.shared_in_collection}
              onChange={(e) => onToggleSharing(annotation.id, e.target.checked)}
            />
            Share with collection
          </label>
        </div>
      </div>

      <div className="replies-section">
        <h4>Discussion ({replies.length})</h4>
        
        {replies.map(reply => (
          <div key={reply.id} className="reply">
            <strong>{reply.user_name}:</strong> {reply.comment}
            <span className="reply-time">
              {new Date(reply.created_at).toLocaleString()}
            </span>
          </div>
        ))}

        <div className="add-reply">
          <input
            type="text"
            value={newReply}
            onChange={(e) => setNewReply(e.target.value)}
            placeholder="Add a reply..."
            onKeyPress={(e) => e.key === 'Enter' && handleAddReply()}
          />
          <button onClick={handleAddReply}>Reply</button>
        </div>
      </div>
    </div>
  );
};
```

## Usage

1. **Share a collection**: Use the existing share collection UI
2. **Enable collaborative annotations**: When creating highlights, toggle "Share with collection"
3. **View collaborators**: See who has access to the collection
4. **Real-time updates**: Annotations sync every 5 seconds (configurable)
5. **Discuss**: Click on any annotation to view/add replies

## Permission Levels

- **Viewer**: Can see shared annotations
- **Commenter**: Can see and reply to annotations
- **Editor**: Can create, edit, and delete annotations
- **Admin**: Full control including managing shares

## Next Steps

To fully implement this feature:

1. Update the existing PDF viewer components to use `annotationSync`
2. Add UI for showing collaborators
3. Add visual indicators for shared vs private annotations
4. Implement WebSocket support for real-time updates (optional)
5. Add notification system for new annotations/replies