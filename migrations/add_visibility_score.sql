-- Add visibility_score column if it doesn't exist
ALTER TABLE image_quality ADD COLUMN visibility_score REAL;

-- Update existing records to use overall score as visibility score
UPDATE image_quality 
SET visibility_score = (clarity_score * 0.6 + composition_score * 0.4)
WHERE visibility_score IS NULL;
