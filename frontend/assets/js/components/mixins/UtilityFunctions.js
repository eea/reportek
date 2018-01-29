export default {
  methods :{
    dateFormat(date, fields) {
      const options = {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: 'numeric',
        minute: 'numeric',
        second: 'numeric',
      };

      if(fields != undefined) {
        Object.keys(options).forEach(function(option, index) {
          if(index > fields) {
            delete options[option]          
          }
        });
      }
      
      const preFormatDate = new Date(date);

      return preFormatDate.toLocaleDateString('en-GB', options);
    },
  },

  filters: {
    capitalize(value) {
      if (!value) {
        return '';
      }
      const result = value.toString();

      return result.charAt(0).toUpperCase() + result.slice(1);
    },
  },
}