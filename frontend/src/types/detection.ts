export interface Detection {
  id: number
  detection_time: string
  common_name: string
  scientific_name: string
  score: number
  frigate_event: string
  visibility_score: number
  clarity_score: number
  composition_score: number
  enhancement_status?: 'pending' | 'completed' | 'failed'
  quality_improvement: number
  enhanced_path?: string
  enhanced_thumbnail_path?: string
  category_name?: string
  camera_name?: string
  detection_index?: number
  is_special?: boolean
  highlight_type?: 'rare' | 'quality' | 'behavior'
  special_score?: number
  community_votes?: number
  featured_status?: number
}
