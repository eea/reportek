export function capitalize(value) {
  if (!value) {
    return '';
  }
  const result = value.toString();

  return result.charAt(0).toUpperCase() + result.slice(1);
}

export function dateFormat(date, fields) {
  if(date){
    const options = {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: 'numeric',
      minute: 'numeric',
      second: 'numeric',
    };

    if (fields != undefined) {
      Object.keys(options).forEach(function(option, index) {
        if (index > fields) {
          delete options[option]
        }
      });
    }

    const preFormatDate = new Date(date);

    return preFormatDate.toLocaleDateString('en-GB', options);
  }
}


export function formatFileSize(bytes,decimalPoint) {
   if(bytes == 0) return '0 Bytes';
   var k = 1000,
       dm = decimalPoint || 2,
       sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'],
       i = Math.floor(Math.log(bytes) / Math.log(k));
   return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}
