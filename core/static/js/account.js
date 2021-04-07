$(document).ready(function(){
	$('.picture-choice').on('click', function(){
		var imagePath = $(this).css('--icon').replaceAll('\\', '');

		console.log(imagePath);

		$('.picture-choice.selected').removeClass('selected');
		$(this).addClass('selected');

		$('.profile-picture-icon').css('--background-image', imagePath);

		imagePath = imagePath.slice(5, imagePath.length - 1).replace('/static/img/profile/', '').replace('-white-100.png', '');

		console.log(imagePath);

		$('#icon-image-path').val(imagePath);
	});
});