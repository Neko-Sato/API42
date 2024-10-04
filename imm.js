/*	
	Intranet magic modification	
	
	This is for pranks when the pisciner leaves the seat without locking the screen.
	Let's add more and more. (do I have time?)
*/


var styleSheet = document.createElement('style');
styleSheet.innerText = `
@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@keyframes reciprocate {
  0% {
    width: 0%
  }
  50% {
    width: 100%
  }
  100% {
    width: 0%
  }
}
`;
document.head.appendChild(styleSheet);

document.querySelectorAll('.profile-image, .user-profile-picture').forEach((element) => {
	element.style.animation = 'rotate 1s linear infinite';
})

document.querySelectorAll('.user-header-box').forEach((element) => {
	element.innerHTML = 'Wooo!!!!';
})

document.querySelectorAll('.progress-bar').forEach((element) => {
	element.style.animation = 'reciprocate 2s linear infinite';
})

document.querySelectorAll('.on-progress').forEach((element) => {
	element.innerText = '🐈ﾆｬｰﾝ';
});

document.querySelectorAll('#user-locations rect').forEach((element) => {
	element.style.transition = 'fill 0.1s ease';
	const changeOpacity = () => {
		element.style.fill = `rgba(0, 186, 188, ${Math.random()})`;
		setTimeout(changeOpacity, Math.floor(Math.random() * 2000) + 100);
	};
	changeOpacity();
});

document.querySelectorAll('.user-action-count').forEach((element) => {
	setInterval(() => {
		var count = Math.floor(Math.random() * 100);
		element.dataset.counterCount = count;
		element.innerText = count;
	}, 100);
});

document.querySelectorAll('#coalition-score .value').forEach((element) => {
	setInterval(() => {
		var count = -Math.floor(Math.random() * 99999);
		element.innerText = count;
	}, 100);
});

document.querySelectorAll('#coalition-rank .value').forEach((element) => {
	element.innerText = "???";
});

document.querySelectorAll('.user-correction-point-value').forEach((element) => {
	setInterval(() => {
		var count = parseInt(element.innerText);
		element.innerText = --count;
	}, 1000);
});

document.querySelectorAll('.user-wallet-value').forEach((element) => {
	element.innerText = "💰🐈ﾆｬｰﾝ";
});


const roate_progress_bar = (event) => {
	document.querySelectorAll('.progress-container').forEach((element) => {
		element.style.animation = 'rotate 2s linear infinite';
	});
	document.removeEventListener('click', roate_progress_bar);
};
document.addEventListener('click', roate_progress_bar);
