import { requireChatGPTUser } from '../chatgpt-auth';
import Studio from './studio';
export const dynamic='force-dynamic';
export default async function Page(){const user=await requireChatGPTUser('/studio');return <Studio displayName={user.displayName}/>;}
