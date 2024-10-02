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
```

42 profile: https://profile.intra.42.fr/users/hshimizu