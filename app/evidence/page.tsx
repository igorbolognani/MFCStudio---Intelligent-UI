import { requireChatGPTUser } from '../chatgpt-auth';
import Evidence from './evidence';
export const dynamic='force-dynamic';
export default async function Page(){await requireChatGPTUser('/evidence');return <Evidence/>;}
