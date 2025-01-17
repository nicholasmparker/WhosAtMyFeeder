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
          <td>{{ detection.detection_time }}</td>
          <td>{{ detection.common_name }}</td>
          <td>{{ detection.score.toFixed(2) }}</td>
          <td>
            <img :src="getThumbnailUrl(detection.frigate_event)" alt="Thumbnail"
                 width="100" height="auto" class="thumbnail"
                 @load="checkTransparentImage"
                 @click="showSnapshot(detection.frigate_event)" />
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
export default {
  props: ['recentDetections'],
  methods: {
    getThumbnailUrl(frigateEvent) {
      return `/frigate/${frigateEvent}/thumbnail.jpg`;
    },
    showSnapshot(frigateEvent) {
      const snapshotUrl = `/frigate/${frigateEvent}/snapshot.jpg`;
      const clipUrl = `/frigate/${frigateEvent}/clip.mp4`;
      // Implement the logic to show the snapshot and clip
    },
    checkTransparentImage(event) {
      // Implement the logic to check for transparent images
    }
  }
}
</script>
