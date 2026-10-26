import {notFound} from 'next/navigation';
import Studio from '../studio/studio';
export const dynamic='force-dynamic';
export default function QA(){if(process.env.NODE_ENV!=='development')notFound();return <Studio displayName="Verificação local"/>;}
