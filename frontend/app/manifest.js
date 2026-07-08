export default function manifest() {
  return {
    name: "Sahel Commerce AI",
    short_name: "Sahel",
    description:
      "Assistant IA de gestion commerciale pour commerçants d'Afrique de l'Ouest",
    start_url: "/",
    display: "standalone",
    background_color: "#0f1115",
    theme_color: "#e8801a",
    lang: "fr",
    icons: [
      {
        src: "/icon.svg",
        sizes: "any",
        type: "image/svg+xml",
        purpose: "any",
      },
      {
        src: "/icon.svg",
        sizes: "any",
        type: "image/svg+xml",
        purpose: "maskable",
      },
    ],
  };
}
