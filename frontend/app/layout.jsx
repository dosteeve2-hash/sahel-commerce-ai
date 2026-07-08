import RegisterSW from "../components/RegisterSW";
import "./globals.css";

export const metadata = {
  title: "Sahel Commerce AI",
  description:
    "Assistant IA de gestion commerciale pour commerçants d'Afrique de l'Ouest",
  manifest: "/manifest.webmanifest",
  icons: { icon: "/icon.svg" },
  appleWebApp: {
    capable: true,
    title: "Sahel",
    statusBarStyle: "black-translucent",
  },
};

export const viewport = {
  themeColor: "#e8801a",
};

export default function RootLayout({ children }) {
  return (
    <html lang="fr">
      <body>
        <RegisterSW />
        {children}
      </body>
    </html>
  );
}
