<script>
	export default {
		onLaunch: function() {
			console.log('App Launch')
			const role = uni.getStorageSync('role');
			  if (role !== 1) {
						console.log('aa')
						uni.setTabBarItem({
							index:2,
							visible:false
						})
			  }
		},
		onShow: function() {
			console.log('App Show')
			const role = uni.getStorageSync('role');
			  if (role !== 1) {
						console.log('aa')
						uni.setTabBarItem({
							index:2,
							visible:false
						})
			  }
		},
		onHide: function() {
			console.log('App Hide')
		}
	}
</script>

<style>
	/*每个页面公共css */
</style>
