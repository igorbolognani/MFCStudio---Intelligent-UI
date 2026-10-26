import type { Metadata } from 'next';
import './globals.css';
export const metadata:Metadata={title:'MFC Studio · Laboratório digital',description:'Configure células a combustível microbianas, investigue relações físicas e acompanhe a evidência de cada hipótese.',icons:{icon:'/favicon.svg'}};
export default function RootLayout({children}:{children:React.ReactNode}) {return <html lang="pt-BR"><body>{children}</body></html>;}
