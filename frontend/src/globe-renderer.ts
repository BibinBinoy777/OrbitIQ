import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import type { TrackPoint } from "./ground-track-api";
import {
  canConnect,
  canRenderPoint,
  displayVector,
  EARTH_POLAR_RATIO,
} from "./globe-geometry";
export type CameraAction =
  "left" | "right" | "up" | "down" | "in" | "out" | "reset" | "focus";
export interface GlobeEngine {
  setData: (points: TrackPoint[], selected: number) => void;
  camera: (action: CameraAction) => void;
  dispose: () => void;
}
export function createGlobe(
  host: HTMLDivElement,
  callbacks: { ready: () => void; lost: () => void; inspect: () => void },
): GlobeEngine {
  const renderer = new THREE.WebGLRenderer({
    antialias: true,
    alpha: true,
    powerPreference: "low-power",
  });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.setClearColor(0x0c1424, 1);
  const canvas = renderer.domElement;
  canvas.setAttribute(
    "aria-label",
    "Interactive Earth in the ITRS frame. Use the labelled camera controls or arrow keys.",
  );
  canvas.setAttribute("role", "img");
  canvas.tabIndex = 0;
  host.append(canvas);
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(42, 1, 0.005, 10000);
  camera.position.set(2.8, 1.5, 2.8);
  const controls = new OrbitControls(camera, canvas);
  controls.enableDamping = false;
  controls.enablePan = false;
  controls.minDistance = 1.25;
  controls.maxDistance = 8;
  const earthGeometry = new THREE.SphereGeometry(1, 64, 32);
  const earthMaterial = new THREE.MeshPhongMaterial({
    color: 0xa9c7dc,
    shininess: 2,
  });
  const earth = new THREE.Mesh(earthGeometry, earthMaterial);
  earth.scale.y = EARTH_POLAR_RATIO;
  scene.add(earth);
  scene.add(new THREE.AmbientLight(0xffffff, 2.0));
  const fill = new THREE.DirectionalLight(0xd8edff, 1.1);
  fill.position.set(4, 3, 4);
  scene.add(fill);
  const markerGeometry = new THREE.SphereGeometry(0.02, 12, 8);
  const markerMaterial = new THREE.MeshBasicMaterial({ color: 0xffd782 });
  const marker = new THREE.Mesh(markerGeometry, markerMaterial);
  marker.visible = false;
  scene.add(marker);
  let groundGeometry = new THREE.BufferGeometry();
  const groundMaterial = new THREE.PointsMaterial({
    color: 0x63d8c7,
    size: 2.5,
    sizeAttenuation: false,
  });
  const groundPoints = new THREE.Points(groundGeometry, groundMaterial);
  scene.add(groundPoints);
  let lineGeometry = new THREE.BufferGeometry();
  const lineMaterial = new THREE.LineBasicMaterial({ color: 0x63d8c7 });
  const lines = new THREE.LineSegments(lineGeometry, lineMaterial);
  scene.add(lines);
  const selectedGeometry = new THREE.SphereGeometry(0.008, 8, 6);
  const selectedMaterial = new THREE.MeshBasicMaterial({ color: 0xffffff });
  const selectedGround = new THREE.Mesh(selectedGeometry, selectedMaterial);
  selectedGround.visible = false;
  scene.add(selectedGround);
  let disposed = false,
    lost = false,
    frame = 0;
  let texture: THREE.Texture | undefined;
  let lastPoints: TrackPoint[] | null = null;
  function invalidate() {
    if (disposed || lost || frame) return;
    frame = requestAnimationFrame(() => {
      frame = 0;
      if (!disposed && !lost) renderer.render(scene, camera);
    });
  }
  function resize() {
    const w = Math.max(host.clientWidth, 1),
      h = Math.max(host.clientHeight, 1);
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    invalidate();
  }
  const resizeObserver = new ResizeObserver(resize);
  resizeObserver.observe(host);
  controls.addEventListener("change", invalidate);
  new THREE.TextureLoader().load(
    "/assets/earth-atmosphere.jpg",
    (t) => {
      if (disposed) {
        t.dispose();
        return;
      }
      texture = t;
      t.colorSpace = THREE.SRGBColorSpace;
      earthMaterial.map = t;
      earthMaterial.color.set(0xffffff);
      earthMaterial.needsUpdate = true;
      invalidate();
    },
    undefined,
    () => invalidate(),
  );
  function action(value: CameraAction) {
    if (disposed || lost) return;
    const spherical = new THREE.Spherical().setFromVector3(
      camera.position.clone().sub(controls.target),
    );
    if (value === "reset") {
      controls.target.set(0, 0, 0);
      camera.position.set(2.8, 1.5, 2.8);
    } else if (value === "focus" && marker.visible) {
      controls.target.set(0, 0, 0);
      camera.position
        .copy(marker.position)
        .normalize()
        .multiplyScalar(Math.max(3.2, marker.position.length() * 2.5));
    } else {
      if (value === "left") spherical.theta -= 0.2;
      if (value === "right") spherical.theta += 0.2;
      if (value === "up") spherical.phi -= 0.15;
      if (value === "down") spherical.phi += 0.15;
      if (value === "in") spherical.radius *= 0.82;
      if (value === "out") spherical.radius /= 0.82;
      spherical.radius = THREE.MathUtils.clamp(
        spherical.radius,
        controls.minDistance,
        controls.maxDistance,
      );
      spherical.phi = THREE.MathUtils.clamp(
        spherical.phi,
        0.02,
        Math.PI - 0.02,
      );
      camera.position.setFromSpherical(spherical).add(controls.target);
    }
    controls.update();
    invalidate();
  }
  function key(e: KeyboardEvent) {
    const binding: Record<string, CameraAction> = {
      ArrowLeft: "left",
      ArrowRight: "right",
      ArrowUp: "up",
      ArrowDown: "down",
      "+": "in",
      "=": "in",
      "-": "out",
      "0": "reset",
    };
    if (binding[e.key]) {
      e.preventDefault();
      action(binding[e.key]);
    }
  }
  const raycaster = new THREE.Raycaster(),
    pointer = new THREE.Vector2();
  let downX = 0,
    downY = 0;
  const down = (e: PointerEvent) => {
    downX = e.clientX;
    downY = e.clientY;
  };
  function up(e: PointerEvent) {
    if (
      lost ||
      !marker.visible ||
      Math.hypot(e.clientX - downX, e.clientY - downY) > 5
    )
      return;
    const rect = canvas.getBoundingClientRect();
    pointer.set(
      ((e.clientX - rect.left) / rect.width) * 2 - 1,
      (-(e.clientY - rect.top) / rect.height) * 2 + 1,
    );
    raycaster.setFromCamera(pointer, camera);
    if (
      raycaster.intersectObjects([earth, marker], false)[0]?.object === marker
    )
      callbacks.inspect();
  }
  function contextLost(e: Event) {
    e.preventDefault();
    lost = true;
    if (frame) {
      cancelAnimationFrame(frame);
      frame = 0;
    }
    callbacks.lost();
  }
  function contextRestored() {
    if (disposed) return;
    lost = false;
    resize();
    callbacks.ready();
  }
  canvas.addEventListener("keydown", key);
  canvas.addEventListener("pointerdown", down);
  canvas.addEventListener("pointerup", up);
  canvas.addEventListener("webglcontextlost", contextLost);
  canvas.addEventListener("webglcontextrestored", contextRestored);
  resize();
  callbacks.ready();
  return {
    camera: action,
    setData(points, selected) {
      const complete =
        points.length > 0 &&
        points.length <= 1000 &&
        points.every(canRenderPoint);
      marker.visible = complete;
      selectedGround.visible = complete;
      if (lastPoints !== points) {
        // Release buffers belonging to the previous dataset before replacing them.
        groundGeometry.dispose();
        lineGeometry.dispose();
        groundGeometry = new THREE.BufferGeometry();
        lineGeometry = new THREE.BufferGeometry();
        groundPoints.geometry = groundGeometry;
        lines.geometry = lineGeometry;
        const ground: number[] = [],
          connections: number[] = [];
        if (complete)
          points.forEach((p, i) => {
            const v = displayVector(p.ground_position_km!).map(
              (x) => x * 1.002,
            );
            ground.push(...v);
            if (i > 0 && canConnect(points[i - 1], p))
              connections.push(
                ...displayVector(points[i - 1].ground_position_km!).map(
                  (x) => x * 1.002,
                ),
                ...v,
              );
          });
        groundGeometry.setAttribute(
          "position",
          new THREE.Float32BufferAttribute(ground, 3),
        );
        groundGeometry.computeBoundingSphere();
        lineGeometry.setAttribute(
          "position",
          new THREE.Float32BufferAttribute(connections, 3),
        );
        lineGeometry.computeBoundingSphere();
      }
      if (complete && points[selected]) {
        marker.position.set(...displayVector(points[selected].position_km!));
        selectedGround.position.set(
          ...(displayVector(points[selected].ground_position_km!).map(
            (x) => x * 1.002,
          ) as [number, number, number]),
        );
        controls.maxDistance = Math.max(8, marker.position.length() * 3);
        if (lastPoints !== points) action("focus");
      } else {
        marker.visible = false;
        selectedGround.visible = false;
      }
      lastPoints = points;
      invalidate();
    },
    dispose() {
      disposed = true;
      if (frame) cancelAnimationFrame(frame);
      resizeObserver.disconnect();
      controls.dispose();
      canvas.removeEventListener("keydown", key);
      canvas.removeEventListener("pointerdown", down);
      canvas.removeEventListener("pointerup", up);
      canvas.removeEventListener("webglcontextlost", contextLost);
      canvas.removeEventListener("webglcontextrestored", contextRestored);
      for (const g of [
        earthGeometry,
        markerGeometry,
        groundGeometry,
        lineGeometry,
        selectedGeometry,
      ])
        g.dispose();
      for (const m of [
        earthMaterial,
        markerMaterial,
        groundMaterial,
        lineMaterial,
        selectedMaterial,
      ])
        m.dispose();
      texture?.dispose();
      renderer.dispose();
      renderer.forceContextLoss();
      canvas.remove();
    },
  };
}
