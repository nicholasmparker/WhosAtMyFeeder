<template>
  <div class="detections-by-hour">
    <div class="container-fluid">
      <div class="row">
        <div class="col-12">
          <h2>Detections for {{ formattedDateTime }}</h2>
          <div v-if="!loading" class="table-responsive">
            <table class="table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Common Name</th>
                  <th>Confidence</th>
                  <th>Image</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="detection in detections" :key="detection.id">
                  <td>{{ formatTime(detection.detection_time) }}</td>
                  <td>{{ detection.common_name }}</td>
                  <td>{{ detection.score.toFixed(2) }}</td>
                  <td>
                    <img 
                      :src="getThumbnailUrl(detection.frigate_event)"
                      alt="Detection thumbnail"
                      class="thumbnail"
                      @click="showSnapshot(detection.frigate_event)"
                      style="cursor: pointer; width: 100px; height: auto;"
                    />
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-else class="text-center">
            <div class="spinner-border" role="status">
              <span class="visually-hidden">Loading...</span>
            </div>
          </div>
        </div>
      </div>
    </div>

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
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import { Modal } from 'bootstrap'

interface Detection {
  id: number
  detection_time: string
  common_name: string
  score: number
  frigate_event: string
}

const route = useRoute()
const loading = ref(true)
const detections = ref<Detection[]>([])
const currentSnapshotUrl = ref('')
const currentClipUrl = ref('')

const formattedDateTime = computed(() => {
  const date = new Date(route.params.date as string)
  const hour = parseInt(route.params.hour as string)
  date.setHours(hour)
  return date.toLocaleString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: 'numeric',
    hour12: true
  })
})

const formatTime = (dateTime: string) => {
  const date = new Date(dateTime)
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: true
  })
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

onMounted(async () => {
  try {
    const response = await axios.get(`/api/detections/by-hour/${route.params.date}/${route.params.hour}`)
    detections.value = response.data
  } catch (error) {
    console.error('Failed to fetch detections:', error)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.detections-by-hour {
  padding: 20px;
}

.thumbnail {
  transition: transform 0.2s;
}

.thumbnail:hover {
  transform: scale(1.1);
}
</style>
