import { useEffect, useState } from "react";
export default function useReducedMotion(onReduce?: () => void) {
  const [reduced, setReduced] = useState(
    () =>
      window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false,
  );
  useEffect(() => {
    const media = window.matchMedia?.("(prefers-reduced-motion: reduce)");
    if (!media) return;
    const update = () => {
      setReduced(media.matches);
      if (media.matches) onReduce?.();
    };
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, [onReduce]);
  return reduced;
}
