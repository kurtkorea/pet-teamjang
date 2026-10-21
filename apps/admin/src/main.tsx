import { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import { Layout, Menu, Card, Button, Space, Tag, Switch, Slider, InputNumber } from "antd";
import {
  DashboardOutlined,
  PlayCircleOutlined,
  StopOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  ArrowLeftOutlined,
  ArrowRightOutlined,
  HomeOutlined,
} from "@ant-design/icons";
import "./style.css";

type InferenceCfg = { imgsz: number; conf: number; iou: number; max_det: number };

const defaultHuman: InferenceCfg = { imgsz: 896, conf: 0.02, iou: 0.8, max_det: 20 };
const defaultDog: InferenceCfg = { imgsz: 768, conf: 0.1, iou: 0.75, max_det: 10 };

function ConfigPanel({
  title,
  cfg,
  setCfg,
  onApply,
}: {
  title: string;
  cfg: InferenceCfg;
  setCfg: (next: InferenceCfg) => void;
  onApply: () => void;
}) {
  return (
    <Card title={title}>
      <Space direction="vertical" className="settings">
        <label>
          imgsz{" "}
          <InputNumber
            min={320}
            max={1280}
            step={32}
            value={cfg.imgsz}
            onChange={(v) => setCfg({ ...cfg, imgsz: v || 640 })}
          />
        </label>
        <label>
          conf
          <Slider min={0.01} max={0.9} step={0.01} value={cfg.conf} onChange={(v) => setCfg({ ...cfg, conf: v })} />
        </label>
        <label>
          iou
          <Slider min={0.1} max={0.95} step={0.05} value={cfg.iou} onChange={(v) => setCfg({ ...cfg, iou: v })} />
        </label>
        <label>
          max_det{" "}
          <InputNumber
            min={1}
            max={50}
            value={cfg.max_det}
            onChange={(v) => setCfg({ ...cfg, max_det: v || 10 })}
          />
        </label>
        <Button type="primary" onClick={onApply}>
          실시간 적용
        </Button>
      </Space>
    </Card>
  );
}

function App() {
  const c = useRef<HTMLCanvasElement>(null);
  const [ds, setDs] = useState<any[]>([]);
  const [live, setLive] = useState(false);
  const [tracking, setTracking] = useState(false);
  const [deadZone, setDeadZone] = useState(0.18);
  const [speed, setSpeed] = useState(0.35);
  const [humanCfg, setHumanCfg] = useState<InferenceCfg>(defaultHuman);
  const [dogCfg, setDogCfg] = useState<InferenceCfg>(defaultDog);
  const [size, setSize] = useState({ width: 960, height: 540 });
  const [streamKey, setStreamKey] = useState(() => Date.now());
  const api = `${location.protocol}//${location.hostname}:3000`;
  const streamSrc = `${location.protocol}//${location.hostname}:8001/stream?t=${streamKey}`;
  const reloadStream = () => setStreamKey(Date.now());

  useEffect(() => {
    const w = new WebSocket(
      `${location.protocol === "https:" ? "wss" : "ws"}://${location.hostname}:3000/ws/detections`,
    );
    w.onmessage = (e) => {
      const d = JSON.parse(e.data);
      setDs(d.detections ?? []);
      if (d.source_width) setSize({ width: d.source_width, height: d.source_height });
    };
    return () => w.close();
  }, []);

  useEffect(() => {
    fetch(`${api}/api/v1/inference/config`)
      .then((r) => r.json())
      .then((data) => {
        if (data.human) setHumanCfg(data.human);
        if (data.dog) setDogCfg(data.dog);
      })
      .catch(() => undefined);
  }, [api]);

  useEffect(() => {
    const img = document.querySelector<HTMLImageElement>("#camera");
    const can = c.current;
    if (!img || !can) return;
    const draw = () => {
      can.width = img.clientWidth;
      can.height = img.clientHeight;
      const x = can.getContext("2d");
      if (!x) return;
      const sx = can.width / size.width;
      const sy = can.height / size.height;
      ds.forEach((d, i) => {
        const [a, b, d2, e] = d.bbox;
        x.strokeStyle = d.label === "dog" ? "#fa8c16" : ["#52c41a", "#1677ff", "#722ed1"][i % 3];
        x.lineWidth = 3;
        x.strokeRect(a * sx, b * sy, (d2 - a) * sx, (e - b) * sy);
        x.fillStyle = x.strokeStyle;
        x.font = "bold 14px Arial";
        x.fillText(
          `${d.dog_id} ${d.behavior ?? "unknown"} ${(d.confidence * 100).toFixed(0)}%`,
          a * sx,
          Math.max(16, b * sy - 6),
        );
      });
    };
    const t = setInterval(draw, 100);
    return () => clearInterval(t);
  }, [ds, size]);

  const post = (p: string, b: any = {}) =>
    fetch(`${api}${p}`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(b) });
  const applyCfg = (target: "human" | "dog", cfg: InferenceCfg) =>
    post("/api/v1/inference/config", { target, ...cfg });
  const toggle = async () => {
    await post(`/api/v1/live/${live ? "stop" : "start"}`);
    if (live) setDs([]);
    else reloadStream();
    setLive(!live);
  };
  const configure = async (v: boolean) => {
    setTracking(v);
    await post("/api/v1/cameras/tc70-01/ptz/auto-track", { enabled: v, dead_zone: deadZone, speed });
  };
  const move = (d: string) => post("/api/v1/cameras/tc70-01/ptz", { direction: d });

  return (
    <Layout className="app">
      <Layout.Sider>
        <div className="brand">
          PET<span>·</span>AI
        </div>
        <Menu
          theme="dark"
          mode="inline"
          defaultSelectedKeys={["monitor"]}
          items={[{ key: "monitor", icon: <DashboardOutlined />, label: "실시간 모니터링" }]}
        />
      </Layout.Sider>
      <Layout>
        <Layout.Header className="topbar">
          <h2>PET 행동분석</h2>
          <Tag color={live ? "green" : "default"}>{live ? "분석 중" : "대기 중"}</Tag>
        </Layout.Header>
        <Layout.Content className="content">
          <Card
            title="실시간 모니터링"
            extra={
              <Button
                type={live ? "default" : "primary"}
                danger={live}
                icon={live ? <StopOutlined /> : <PlayCircleOutlined />}
                onClick={toggle}
              >
                {live ? "분석 중지" : "분석 시작"}
              </Button>
            }
          >
            <div className="viewer">
              <img
                id="camera"
                key={streamKey}
                src={streamSrc}
                alt="CCTV"
                onError={() => window.setTimeout(reloadStream, 1000)}
              />
              <canvas ref={c} />
            </div>
            <p>검출 대상: {ds.length}마리</p>
          </Card>
          <div className="grid">
            <Card title="카메라 제어">
              <div className="ptz">
                <Button icon={<ArrowUpOutlined />} onClick={() => move("up")} />
                <Space>
                  <Button icon={<ArrowLeftOutlined />} onClick={() => move("left")} />
                  <Button icon={<HomeOutlined />} onClick={() => move("home")} />
                  <Button icon={<ArrowRightOutlined />} onClick={() => move("right")} />
                </Space>
                <Button icon={<ArrowDownOutlined />} onClick={() => move("down")} />
              </div>
            </Card>
            <Card title="자동 추적 설정">
              <Space direction="vertical" className="settings">
                <Switch checked={tracking} onChange={configure} checkedChildren="ON" unCheckedChildren="OFF" />
                <label>
                  Dead-zone
                  <Slider min={0.05} max={0.5} step={0.01} value={deadZone} onChange={setDeadZone} />
                </label>
                <label>
                  이동 속도
                  <Slider min={0.1} max={1} step={0.05} value={speed} onChange={setSpeed} />
                </label>
              </Space>
            </Card>
            <ConfigPanel
              title="사람 분석 파라미터"
              cfg={humanCfg}
              setCfg={setHumanCfg}
              onApply={() => applyCfg("human", humanCfg)}
            />
            <ConfigPanel
              title="강아지 분석 파라미터"
              cfg={dogCfg}
              setCfg={setDogCfg}
              onApply={() => applyCfg("dog", dogCfg)}
            />
          </div>
        </Layout.Content>
      </Layout>
    </Layout>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
