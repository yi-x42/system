import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Target } from "lucide-react";
import apiClient from "../lib/api";

interface CameraMeta {
  id: string;
  name: string;
  device_index?: number;
  device_id?: string;
  list_index?: number;
}

interface DetectionBox {
  bbox: [number, number, number, number];
  label?: string;
  confidence?: number;
  tracker_id?: number;
}

export interface DetectionFrame {
  detections: DetectionBox[];
  width: number;
  height: number;
  image?: string;
  timestamp?: number;
}

interface RealtimePreviewProps {
  running?: boolean;
  cameraName?: string;
  cameraInfo?: CameraMeta | null;
  detectionFrame?: DetectionFrame | null;
  taskId?: string | null;
  onDevicesUpdated?: (devices: MediaDeviceInfo[]) => void;
  onUploadError?: (message: string) => void;
}

const buildWebSocketUrl = (targetPath: string) => {
  const base = apiClient.defaults.baseURL || `${window.location.origin}/api/v1`;
  let baseUrl: URL;
  try {
    baseUrl = new URL(base);
  } catch {
    baseUrl = new URL(`${window.location.origin}/api/v1`);
  }

  const origin = baseUrl.origin;
  const apiPrefix = baseUrl.pathname.replace(/\/$/, "");

  const ensureLeadingSlash = (value: string) => (value.startsWith("/") ? value : `/${value}`);
  const normalizePath = (value: string) => {
    const withSlash = ensureLeadingSlash(value);
    if (!apiPrefix || withSlash.startsWith(apiPrefix)) {
      return withSlash;
    }
    return `${apiPrefix}${withSlash}`.replace(/\/{2,}/g, "/");
  };

  if (/^wss?:\/\//i.test(targetPath)) {
    return targetPath;
  }
  if (/^https?:\/\//i.test(targetPath)) {
    const directUrl = new URL(targetPath);
    directUrl.protocol = directUrl.protocol === "https:" ? "wss:" : "ws:";
    directUrl.search = "";
    directUrl.hash = "";
    return directUrl.toString();
  }

  const url = new URL(normalizePath(targetPath), origin);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  url.search = "";
  url.hash = "";
  return url.toString();
};

const RealtimePreview = ({
  running = false,
  cameraName,
  cameraInfo,
  detectionFrame,
  taskId,
  onDevicesUpdated,
  onUploadError,
}: RealtimePreviewProps) => {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const overlayCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const captureCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const uploadSocketRef = useRef<WebSocket | null>(null);
  const frameTimerRef = useRef<number | null>(null);
  const retryTimerRef = useRef<number | null>(null);
  const runningRef = useRef<boolean>(false);
  const intentionalCloseRef = useRef<boolean>(false);
  const [statusMessage, setStatusMessage] = useState<string>("開始分析後顯示即時預覽");
  const [videoDevices, setVideoDevices] = useState<MediaDeviceInfo[]>([]);
  const [uploadAttempt, setUploadAttempt] = useState(0);
  const uploadErrorRef = useRef(onUploadError);

  useEffect(() => {
    uploadErrorRef.current = onUploadError;
  }, [onUploadError]);

  const detections = useMemo(() => detectionFrame?.detections ?? [], [detectionFrame]);

  const stopLocalStream = useCallback(() => {
    const stream = streamRef.current;
    if (stream) {
      stream.getTracks().forEach((track) => {
        try {
          track.stop();
        } catch {
          /* ignore */
        }
      });
      streamRef.current = null;
    }
    const video = videoRef.current;
    if (video) {
      video.srcObject = null;
    }
  }, []);

  const closeUploadSocket = useCallback(() => {
    if (frameTimerRef.current !== null) {
      window.clearInterval(frameTimerRef.current);
      frameTimerRef.current = null;
    }
    if (retryTimerRef.current !== null) {
      window.clearTimeout(retryTimerRef.current);
      retryTimerRef.current = null;
    }
    const socket = uploadSocketRef.current;
    uploadSocketRef.current = null;
    if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
      intentionalCloseRef.current = true;
      try {
        socket.close();
      } catch {
        /* ignore */
      }
    }
  }, []);

  useEffect(() => {
    runningRef.current = running;
  }, [running]);

  useEffect(() => {
    if (!navigator.mediaDevices?.enumerateDevices) {
      return;
    }

    const updateDevices = () => {
      navigator.mediaDevices
        .enumerateDevices()
        .then((devices) => {
          const videoOnly = devices.filter((device) => device.kind === "videoinput");
          setVideoDevices(videoOnly);
          onDevicesUpdated?.(videoOnly);
        })
        .catch(() => {
          /* ignore */
        });
    };

    updateDevices();
    navigator.mediaDevices.addEventListener("devicechange", updateDevices);
    return () => {
      navigator.mediaDevices.removeEventListener("devicechange", updateDevices);
    };
  }, [onDevicesUpdated]);

  useEffect(() => {
    if (!running || !cameraInfo) {
      stopLocalStream();
      setStatusMessage("開始分析後顯示即時預覽");
      return;
    }

    const startPreview = async () => {
      if (!navigator.mediaDevices?.getUserMedia) {
        setStatusMessage("瀏覽器不支援攝影機存取");
        return;
      }

      setStatusMessage("取得本機攝影機畫面中…");

      const constraints: MediaStreamConstraints = {
        video: true,
        audio: false,
      };

      let targetDeviceId = cameraInfo.device_id;
      if (!targetDeviceId && videoDevices.length > 0) {
        const numericIndex =
          typeof cameraInfo.device_index === "number" && Number.isFinite(cameraInfo.device_index)
            ? Math.trunc(cameraInfo.device_index)
            : cameraInfo.list_index ?? 0;
        const boundedIndex =
          ((numericIndex % videoDevices.length) + videoDevices.length) % videoDevices.length;
        targetDeviceId = videoDevices[boundedIndex]?.deviceId;
      }

      let finalConstraints = constraints;
      if (targetDeviceId) {
        finalConstraints = {
          ...constraints,
          video: {
            ...(typeof constraints.video === "object" ? constraints.video : {}),
            deviceId: { exact: targetDeviceId },
          },
        };
      }

      try {
        const stream = await navigator.mediaDevices.getUserMedia(finalConstraints);
        stopLocalStream();
        streamRef.current = stream;
        const video = videoRef.current;
        if (video) {
          video.srcObject = stream;
          await video.play().catch(() => {
            /* autoplay blocked */
          });
        }
        setStatusMessage("");
      } catch (error) {
        console.error("取得本機攝影機畫面失敗:", error);
        setStatusMessage("無法取得攝影機畫面");
        uploadErrorRef.current?.("無法取得攝影機畫面");
        stopLocalStream();
      }
    };

    startPreview();
    return () => {
      stopLocalStream();
    };
  }, [running, cameraInfo, videoDevices, stopLocalStream]);

  const drawDetections = useCallback(() => {
    const video = videoRef.current;
    const canvas = overlayCanvasRef.current;
    if (!video || !canvas) {
      return;
    }

    const ctx = canvas.getContext("2d");
    if (!ctx) {
      return;
    }

    const displayWidth = video.clientWidth || video.videoWidth;
    const displayHeight = video.clientHeight || video.videoHeight;
    if (!displayWidth || !displayHeight) {
      return;
    }

    if (canvas.width !== displayWidth || canvas.height !== displayHeight) {
      canvas.width = displayWidth;
      canvas.height = displayHeight;
    }

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (!running || !detectionFrame || detections.length === 0) {
      return;
    }

    const sourceWidth = detectionFrame.width || video.videoWidth || displayWidth;
    const sourceHeight = detectionFrame.height || video.videoHeight || displayHeight;
    if (!sourceWidth || !sourceHeight) {
      return;
    }

    const scaleX = displayWidth / sourceWidth;
    const scaleY = displayHeight / sourceHeight;

    ctx.lineWidth = 2;
    ctx.font = "14px sans-serif";
    ctx.textBaseline = "top";

    detections.forEach((detection) => {
      const [x1, y1, x2, y2] = detection.bbox;
      const left = x1 * scaleX;
      const top = y1 * scaleY;
      const width = (x2 - x1) * scaleX;
      const height = (y2 - y1) * scaleY;

      ctx.strokeStyle = "#22d3ee";
      ctx.fillStyle = "rgba(34, 211, 238, 0.15)";
      ctx.fillRect(left, top, width, height);
      ctx.strokeRect(left, top, width, height);

      const labelParts: string[] = [];
      if (detection.label) {
        labelParts.push(detection.label);
      }
      if (typeof detection.confidence === "number") {
        labelParts.push(`${Math.round(detection.confidence * 100)}%`);
      }
      const label = labelParts.join(" • ");

      if (label) {
        const padding = 4;
        const metrics = ctx.measureText(label);
        const textWidth = metrics.width + padding * 2;
        const textHeight = 16 + padding;

        ctx.fillStyle = "rgba(15, 23, 42, 0.85)";
        ctx.fillRect(left, Math.max(top - textHeight, 0), textWidth, textHeight);

        ctx.fillStyle = "#f8fafc";
        ctx.fillText(label, left + padding, Math.max(top - textHeight + padding / 2, 0));
      }
    });
  }, [detections, detectionFrame, running]);

  useEffect(() => {
    drawDetections();
  }, [drawDetections, detections, detectionFrame]);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) {
      return;
    }

    const handleLoadedMetadata = () => {
      drawDetections();
    };

    video.addEventListener("loadedmetadata", handleLoadedMetadata);

    let observer: ResizeObserver | undefined;
    if (typeof ResizeObserver !== "undefined") {
      observer = new ResizeObserver(() => drawDetections());
      observer.observe(video);
    }

    return () => {
      video.removeEventListener("loadedmetadata", handleLoadedMetadata);
      observer?.disconnect();
    };
  }, [drawDetections]);

  const captureAndSendFrame = useCallback(() => {
    const socket = uploadSocketRef.current;
    const video = videoRef.current;
    const captureCanvas = captureCanvasRef.current;

    if (!socket || socket.readyState !== WebSocket.OPEN || !video || !captureCanvas) {
      return;
    }

    if (video.readyState < HTMLMediaElement.HAVE_CURRENT_DATA) {
      return;
    }

    const width = video.videoWidth || video.clientWidth;
    const height = video.videoHeight || video.clientHeight;
    if (!width || !height) {
      return;
    }

    captureCanvas.width = width;
    captureCanvas.height = height;

    const ctx = captureCanvas.getContext("2d");
    if (!ctx) {
      return;
    }

    ctx.drawImage(video, 0, 0, width, height);
    const dataUrl = captureCanvas.toDataURL("image/jpeg", 0.65);
    const base64Data = dataUrl.split(",")[1] ?? dataUrl;

    try {
      socket.send(
        JSON.stringify({
          type: "frame",
          image: base64Data,
          width,
          height,
        })
      );
    } catch (error) {
      console.warn("傳送即時分析影像失敗:", error);
    }
  }, []);

  useEffect(() => {
    if (!running || !taskId) {
      closeUploadSocket();
      if (uploadAttempt !== 0) {
        setUploadAttempt(0);
      }
      return;
    }

    const existing = uploadSocketRef.current;
    if (existing && (existing.readyState === WebSocket.OPEN || existing.readyState === WebSocket.CONNECTING)) {
      return;
    }

    const url = buildWebSocketUrl(`/frontend/analysis/live-person-camera/${taskId}/upload`);
    const socket = new WebSocket(url);
    uploadSocketRef.current = socket;

    socket.onopen = () => {
      if (frameTimerRef.current !== null) {
        window.clearInterval(frameTimerRef.current);
      }
      frameTimerRef.current = window.setInterval(() => {
        captureAndSendFrame();
      }, 200);
    };

    socket.onerror = (event) => {
      console.error("Live Person Camera 影像上傳 WebSocket 發生錯誤:", event);
      uploadErrorRef.current?.("影像上傳連線發生錯誤");
    };

    socket.onclose = () => {
      if (frameTimerRef.current !== null) {
        window.clearInterval(frameTimerRef.current);
        frameTimerRef.current = null;
      }
      if (uploadSocketRef.current === socket) {
        uploadSocketRef.current = null;
      }
      if (retryTimerRef.current !== null) {
        window.clearTimeout(retryTimerRef.current);
        retryTimerRef.current = null;
      }
      const intentional = intentionalCloseRef.current;
      intentionalCloseRef.current = false;
      if (!intentional && runningRef.current) {
        retryTimerRef.current = window.setTimeout(() => {
          setUploadAttempt((attempt) => attempt + 1);
        }, 500);
      }
    };

    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload?.type === "error") {
          console.warn("Live Person Camera 上傳回傳錯誤:", payload.message);
        }
      } catch {
        /* ignore */
      }
    };

    return () => {
      closeUploadSocket();
    };
  }, [running, taskId, uploadAttempt, captureAndSendFrame, closeUploadSocket]);

  useEffect(() => {
    if (!running) {
      const canvas = overlayCanvasRef.current;
      if (canvas) {
        const ctx = canvas.getContext("2d");
        ctx?.clearRect(0, 0, canvas.width, canvas.height);
      }
    }
  }, [running]);

  return (
    <div className="relative aspect-video overflow-hidden rounded-lg bg-black">
      <video
        ref={videoRef}
        className="h-full w-full"
        autoPlay
        playsInline
        muted
        style={{ width: "100%", height: "100%", display: "block" }}
      />
      <canvas ref={overlayCanvasRef} className="absolute inset-0 pointer-events-none" />
      <canvas ref={captureCanvasRef} className="hidden" />
      {statusMessage && (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-black/60 text-white">
          <Target className="h-12 w-12 opacity-60" />
          <p className="text-base">{statusMessage}</p>
          {cameraName && <p className="text-xs opacity-70">{cameraName}</p>}
        </div>
      )}
    </div>
  );
};

export default RealtimePreview;

