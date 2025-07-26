/**
 * Collaborative annotation synchronization with backend
 */

import { API_BASE_URL } from './api';

export interface CollaborativeAnnotation {
  id: string;
  paper_id: string;
  collection_id?: string;
  user_id: string;
  user_name?: string;
  annotation_type: 'highlight' | 'comment' | 'note';
  color: string;
  page_number: number;
  position_x: number;
  position_y: number;
  width: number;
  height: number;
  selected_text: string;
  comment?: string;
  is_private: boolean;
  shared_in_collection: boolean;
  created_at: string;
  updated_at: string;
}

export interface AnnotationReply {
  id: string;
  annotation_id: string;
  user_id: string;
  user_name?: string;
  comment: string;
  parent_reply_id?: string;
  created_at: string;
}

export interface Collaborator {
  id: string;
  name: string;
  email: string;
  role: 'owner' | 'viewer' | 'commenter' | 'editor' | 'admin';
  avatar_url?: string;
}

class AnnotationSyncService {
  private authToken: string | null = null;

  setAuthToken(token: string) {
    this.authToken = token;
  }

  private getHeaders() {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };
    if (this.authToken) {
      headers['Authorization'] = `Bearer ${this.authToken}`;
    }
    return headers;
  }

  async createAnnotation(annotation: {
    paper_id: string;
    collection_id?: string;
    annotation_type: 'highlight' | 'comment' | 'note';
    color: string;
    page_number: number;
    position_x: number;
    position_y: number;
    width: number;
    height: number;
    selected_text: string;
    comment?: string;
    is_private?: boolean;
    shared_in_collection?: boolean;
  }): Promise<CollaborativeAnnotation> {
    const response = await fetch(`${API_BASE_URL}/api/annotations`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(annotation),
    });

    if (!response.ok) {
      throw new Error('Failed to create annotation');
    }

    return response.json();
  }

  async getAnnotations(
    paperId: string,
    collectionId?: string,
    includeShared: boolean = true
  ): Promise<CollaborativeAnnotation[]> {
    const params = new URLSearchParams({
      include_shared: includeShared.toString(),
    });
    
    if (collectionId) {
      params.append('collection_id', collectionId);
    }

    const response = await fetch(
      `${API_BASE_URL}/api/papers/${paperId}/annotations?${params}`,
      {
        headers: this.getHeaders(),
      }
    );

    if (!response.ok) {
      if (response.status === 403) {
        throw new Error('No access to this collection');
      }
      throw new Error('Failed to fetch annotations');
    }

    return response.json();
  }

  async updateAnnotation(
    annotationId: string,
    updates: {
      comment?: string;
      color?: string;
      is_private?: boolean;
      shared_in_collection?: boolean;
    }
  ): Promise<CollaborativeAnnotation> {
    const response = await fetch(
      `${API_BASE_URL}/api/annotations/${annotationId}`,
      {
        method: 'PUT',
        headers: this.getHeaders(),
        body: JSON.stringify(updates),
      }
    );

    if (!response.ok) {
      throw new Error('Failed to update annotation');
    }

    return response.json();
  }

  async deleteAnnotation(annotationId: string): Promise<void> {
    const response = await fetch(
      `${API_BASE_URL}/api/annotations/${annotationId}`,
      {
        method: 'DELETE',
        headers: this.getHeaders(),
      }
    );

    if (!response.ok) {
      throw new Error('Failed to delete annotation');
    }
  }

  async addReply(
    annotationId: string,
    comment: string,
    parentReplyId?: string
  ): Promise<AnnotationReply> {
    const response = await fetch(
      `${API_BASE_URL}/api/annotations/${annotationId}/replies`,
      {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({
          comment,
          parent_reply_id: parentReplyId,
        }),
      }
    );

    if (!response.ok) {
      throw new Error('Failed to add reply');
    }

    return response.json();
  }

  async getReplies(annotationId: string): Promise<AnnotationReply[]> {
    const response = await fetch(
      `${API_BASE_URL}/api/annotations/${annotationId}/replies`,
      {
        headers: this.getHeaders(),
      }
    );

    if (!response.ok) {
      throw new Error('Failed to fetch replies');
    }

    return response.json();
  }

  async getCollaborators(collectionId: string): Promise<Collaborator[]> {
    const response = await fetch(
      `${API_BASE_URL}/api/collections/${collectionId}/collaborators`,
      {
        headers: this.getHeaders(),
      }
    );

    if (!response.ok) {
      throw new Error('Failed to fetch collaborators');
    }

    return response.json();
  }

  // Real-time sync using polling (can be replaced with WebSocket later)
  startSync(
    paperId: string,
    collectionId: string | undefined,
    onUpdate: (annotations: CollaborativeAnnotation[]) => void,
    interval: number = 5000
  ): () => void {
    let timeoutId: NodeJS.Timeout;

    const sync = async () => {
      try {
        const annotations = await this.getAnnotations(paperId, collectionId);
        onUpdate(annotations);
      } catch (error) {
        console.error('Sync error:', error);
      }
      
      timeoutId = setTimeout(sync, interval);
    };

    sync();

    // Return cleanup function
    return () => {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }
}

export const annotationSync = new AnnotationSyncService();