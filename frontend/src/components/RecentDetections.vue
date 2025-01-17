<template>
  <div>
    <h2>Recent Detections</h2>
    <table class="table">
      <thead>
        <tr>
          <th scope="col">Detection Time</th>
          <th scope="col">Common Name</th>
          <th scope="col">Confidence</th>
          <th scope="col">Thumbnail</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="detection in recentDetections" :key="detection.id">
          <td>{{ formatDateTime(detection.detection_time) }}</td>
          <td>{{ detection.common_name }}</td>
          <td>{{ detection.score.toFixed(2) }}</td>
          <td>
            <img 
              :src="getThumbnailUrl(detection.frigate_event)" 
              alt="Thumbnail"
              width="100" 
              height="auto" 
              class="thumbnail"
              @load="checkTransparentImage"
              @click="showSnapshot(detection.frigate_event)"
              style="cursor: pointer"
            />
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Modal for displaying snapshot -->
    <div class="modal fade" id="snapshotModal" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Detection Snapshot</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body text-center">
            <img :src="currentSnapshotUrl" alt="Detection Snapshot" class="img-fluid" />
            <div class="mt-3">
              <a :href="currentClipUrl" class="btn btn-primary" target="_blank">View Clip</a>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Modal } from 'bootstrap'

interface Props {
  recentDetections: {
    id: number
    detection_time: string
    common_name: string
    score: number
    frigate_event: string
  }[]
}

const props = defineProps<Props>()
const currentSnapshotUrl = ref('')
const currentClipUrl = ref('')

const formatDateTime = (dateTime: string) => {
  const date = new Date(dateTime)
  return date.toLocaleString()
}

const getThumbnailUrl = (frigateEvent: string) => {
  return `/frigate/${frigateEvent}/thumbnail.jpg`
}

const showSnapshot = (frigateEvent: string) => {
  currentSnapshotUrl.value = `/frigate/${frigateEvent}/snapshot.jpg`
  currentClipUrl.value = `/frigate/${frigateEvent}/clip.mp4`
  const modal = new Modal(document.getElementById('snapshotModal')!)
  modal.show()
}

const checkTransparentImage = (event: Event) => {
  const img = event.target as HTMLImageElement
  // Add logic here if needed to handle transparent images
}
</script>

<style scoped>
.thumbnail {
  transition: transform 0.2s;
}

.thumbnail:hover {
  transform: scale(1.1);
}
</style>
