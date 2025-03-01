# Project Overview

This project was independently created by lifesaver hshimizu during the Piscine at 42Tokyo to allow lifeservers to monitor the progress of pisciners' tasks.

It includes functionalities for easily interacting with the API and various other scripts.

Of course, you can understand what it does just by looking at the code, so there are no explanations provided.

Very, very important and should be said,
PISCINER should not be misled by rankings.

Peer to peer is what piscine and 42 are about, not competing, in my opinion.
And let's not let pisciner give up.

I also have my own idea that pisciner should not be structured so that a lagging pisciner always asks questions to the top tier, but rather discusses with others who are at the same level or a little more advanced than him or herself and takes a fun detour.

Let's help them enjoy piscine without rushing too much.

```
git clone https://github.com/Neko-Sato/API42.git
cd API42
pip install -r API42/requirements.txt
export API42_CLIENT_ID=[YOUR_CLIENT_ID]
export API42_CLIENT_SECRET=[YOUR_CLIENT_SECRET]
./get_pisciners.py
./rank.py pisciners_*.json
cat rank.txt
```

(Additional Note)
At first, I thought this would help understand the state of pisciners.
However, in the first week, everyone was at level 0, so there was no visible difference.
Moreover, pisciners are active, and the existing events are sufficient for communication-based support. Those who struggle even with that are not suited for attending 42 School.

A more effective use of this would be to present examples of past pisciners in a way that is easier to view and compare than on the intranet.
To prevent pisciners from feeling hopeless due to the gap with the top tier, as long as their current situation is not too bad, we can convince them that the evaluation criteria are unclear but that they might still pass.

（2025/03/01）
I got fired from 42tokyo's lifesaver. It is very sad. But they need to respect their ideas. I am convinced of it. Everyone would have thought it was a bit terrible. It can't be helped. I hope all pisciner swim through and be one of us.


42 profile: https://profile.intra.42.fr/users/hshimizu
