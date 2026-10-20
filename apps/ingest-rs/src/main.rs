use std::{env, path::PathBuf, process::Stdio, time::Duration};
use chrono::Local;
use tokio::{process::{Child, Command}, time::sleep};
use tracing::{error, info, warn};

fn required_env(name: &str) -> String {
    env::var(name).unwrap_or_else(|_| panic!("{name} must be set"))
}

fn output_pattern(root: &str) -> PathBuf {
    let now = Local::now();
    PathBuf::from(root)
        .join(now.format("%Y/%m/%d").to_string())
        .join("%Y%m%d_%H%M%S.mp4")
}

fn spawn_ffmpeg(rtsp_url: &str, output: &str, segment_seconds: &str) -> Child {
    Command::new("ffmpeg")
        .args([
            "-hide_banner", "-loglevel", "warning", "-rtsp_transport", "tcp",
            "-i", rtsp_url, "-map", "0:v:0", "-an", "-c:v", "copy",
            "-f", "segment", "-segment_time", segment_seconds,
            "-reset_timestamps", "1", "-strftime", "1", output,
        ])
        .stdout(Stdio::null())
        .stderr(Stdio::inherit())
        .spawn()
        .expect("failed to start ffmpeg; install ffmpeg and add it to PATH")
}

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt::init();
    let rtsp_url = required_env("RTSP_URL");
    let output_root = env::var("OUTPUT_DIR").unwrap_or_else(|_| "./data/recordings".into());
    let segment_seconds = env::var("SEGMENT_SECONDS").unwrap_or_else(|_| "60".into());
    std::fs::create_dir_all(&output_root).expect("failed to create output directory");
    info!(%output_root, "video ingest service started");

    loop {
        let pattern = output_pattern(&output_root);
        if let Some(parent) = pattern.parent() {
            std::fs::create_dir_all(parent).expect("failed to create dated output directory");
        }
        let output = pattern.to_string_lossy().replace('\\', "/");
        let mut ffmpeg = spawn_ffmpeg(&rtsp_url, &output, &segment_seconds);
        tokio::select! {
            result = ffmpeg.wait() => {
                match result {
                    Ok(status) => warn!(%status, "ffmpeg stopped; reconnecting"),
                    Err(err) => error!(%err, "ffmpeg process error; reconnecting"),
                }
                sleep(Duration::from_secs(5)).await;
            }
            _ = tokio::signal::ctrl_c() => {
                info!("shutdown requested");
                let _ = ffmpeg.kill().await;
                break;
            }
        }
    }
}
