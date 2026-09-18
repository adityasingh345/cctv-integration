import { useEffect, useRef } from "react";
import Hls from "hls.js";
import { HLS } from "../api";

function VideoTile({ camera }) {
  const videoRef = useRef(null);
  // camera rtsp url ends in /camNNN -> HLS stream is at HLS/camNNN/index.m3u8
  const streamName = (camera.rtsp_url || "").split("/").pop();
  const src = `${HLS}/${streamName}/index.m3u8`;

  useEffect(() => {
    const video = videoRef.current;
    if (!video || !streamName) return;
    let hls;
    if (Hls.isSupported()) {
      hls = new Hls({ liveDurationInfinity: true });
      hls.loadSource(src);
      hls.attachMedia(video);
    } else if (video.canPlayType("application/vnd.apple.mpegurl")) {
      video.src = src; // Safari
    }
    return () => hls?.destroy();
  }, [src, streamName]);

  return (
    <div className="tile">
      <video ref={videoRef} muted autoPlay playsInline />
      <span className="tile-label">{camera.camera_code}</span>
    </div>
  );
}

export default function VideoGrid({ cameras }) {
  return (
    <div className="video-grid">
      {cameras.map((c) => <VideoTile key={c.id} camera={c} />)}
    </div>
  );
}