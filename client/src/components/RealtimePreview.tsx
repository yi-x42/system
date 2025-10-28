import { useEffect, useRef, useState } from "react";
import { Target } from "lucide-react";
import apiClient from "../lib/api";

interface RealtimePreviewProps {
  taskId?: string | null;
  running?: boolean;
  cameraName?: string;
  onCommandReady?: (sender: ((name: string, value: boolean) => void) | null) => void;
}

const iceGatheringComplete = (pc: RTCPeerConnection) =>
  new Promise<void>((resolve) => {
    if (pc.iceGatheringState === "complete") {
      resolve();
      return;
    }
    const checkState = () => {
      if (pc.iceGatheringState === "complete") {
        pc.removeEventListener("icegatheringstatechange", checkState);
        resolve();
      }
    };
    pc.addEventListener("icegatheringstatechange", checkState);
  });

const RealtimePreview = ({
  taskId,
  running = false,
  cameraName,
  onCommandReady,
}: RealtimePreviewProps) => {
  console.log("[RealtimePreview] render", { taskId, running });

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const peerRef = useRef<RTCPeerConnection | null>(null);
  const dataChannelRef = useRef<RTCDataChannel | null>(null);
  const [statusMessage, setStatusMessage] = useState<string>("開始分析後顯示即時預覽");

  useEffect(() => {
    let isActive = true;

    const cleanup = async () => {
      if (onCommandReady) {
        onCommandReady(null);
      }

      if (dataChannelRef.current) {
        try {
          dataChannelRef.current.close();
        } catch {
          /* ignore */
        }
        dataChannelRef.current = null;
      }

      if (peerRef.current) {
        try {
          await peerRef.current.close();
        } catch {
          /* ignore */
        }
        peerRef.current = null;
      }

      const video = videoRef.current;
      if (video) {
        video.srcObject = null;
      }
    };

    if (!running || !taskId) {
      cleanup().finally(() => {
        if (isActive) {
          setStatusMessage("開始分析後顯示即時預覽");
        }
      });
      return () => {
        isActive = false;
      };
    }

    const startConnection = async () => {
      console.log("[RealtimePreview] start connection", taskId);
      setStatusMessage("連線中…");

      const pc = new RTCPeerConnection({
        iceServers: [],
      });
      peerRef.current = pc;

      pc.onconnectionstatechange = () => {
        if (!isActive) {
          return;
        }
        if (pc.connectionState === "connected") {
          setStatusMessage("");
        } else if (pc.connectionState === "connecting") {
          setStatusMessage("連線中…");
        } else if (
          pc.connectionState === "disconnected" ||
          pc.connectionState === "failed"
        ) {
          setStatusMessage("連線中斷，重新嘗試中…");
        }
      };

      pc.oniceconnectionstatechange = () => {
        if (!isActive) {
          return;
        }
        if (pc.iceConnectionState === "failed") {
          setStatusMessage("ICE 連線失敗");
        }
      };

      pc.ontrack = (event) => {
        if (!isActive) {
          return;
        }
        const [stream] = event.streams;
        const video = videoRef.current;
        if (video) {
          video.srcObject = stream;
        }
      };

      pc.addTransceiver("video", { direction: "recvonly" });
      const controlChannel = pc.createDataChannel("control");
      dataChannelRef.current = controlChannel;

      controlChannel.onopen = () => {
        if (!isActive) {
          return;
        }
        setStatusMessage("");
        if (onCommandReady) {
          onCommandReady((name, value) => {
            if (controlChannel.readyState === "open") {
              controlChannel.send(
                JSON.stringify({ type: "toggle", name, value })
              );
            }
          });
        }
      };

      controlChannel.onclose = () => {
        if (onCommandReady) {
          onCommandReady(null);
        }
      };

      pc.ondatachannel = (event) => {
        const channel = event.channel;
        if (channel.label !== "control") {
          return;
        }
        dataChannelRef.current = channel;
        channel.onopen = () => {
          if (!isActive) {
            return;
          }
          setStatusMessage("");
          if (onCommandReady) {
            onCommandReady((name, value) => {
              if (channel.readyState === "open") {
                channel.send(JSON.stringify({ type: "toggle", name, value }));
              }
            });
          }
        };
        channel.onclose = () => {
          if (onCommandReady) {
            onCommandReady(null);
          }
        };
      };

      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);
      await iceGatheringComplete(pc);

      const localDescription = pc.localDescription;
      if (!localDescription) {
        throw new Error("無法建立本地 SDP");
      }

      const { data } = await apiClient.post(
        `/frontend/analysis/live-person-camera/${taskId}/webrtc`,
        {
          sdp: localDescription.sdp,
          type: localDescription.type,
        }
      );
      const remoteDescription = new RTCSessionDescription(data);
      await pc.setRemoteDescription(remoteDescription);

      setStatusMessage("");
    };

    startConnection().catch((error) => {
      console.error("建立 WebRTC 連線失敗:", error);
      setStatusMessage("建立 WebRTC 連線失敗");
    });

    return () => {
      isActive = false;
      cleanup();
    };
  }, [running, taskId, onCommandReady]);

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
