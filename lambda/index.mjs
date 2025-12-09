export const handler = async (event) => {
    try {
        // 详细的日志记录
        //console.log('Event received:', JSON.stringify(event, null, 2));

        if (!event.Records?.[0]?.cf?.request) {
            throw new Error('Invalid event structure: missing request object');
        }

        const request = event.Records[0].cf.request;
        const headers = request.headers;
        const authHeader = headers.authorization?.[0]?.value;
        if (!authHeader) {
            return request;
        }

        // 解析区域信息
        const credentialMatch = authHeader.match(/Credential=([^/]+)\/([^/]+)\/([^/]+)/);
        if (!credentialMatch || !credentialMatch[3]) {
            console.log('No region found in Authorization header');
            return request;
        }

        const region = credentialMatch[3];

        // 记录原始请求头
        //console.log('Original headers:', JSON.stringify(request.headers, null, 2));

        // 安全地删除 header
        if (request.headers && request.headers['x-forwarded-for']) {
            console.log('Removing x-forwarded-for header');
            delete request.headers['x-forwarded-for'];
        }
        
        request.headers['user-agent'] = [{
            key: 'User-Agent',
            value: `cloudfront`
        }];


        // 设置新的源域名
        request.origin = {
            custom: {
                domainName: `bedrock-runtime.${region}.amazonaws.com`,
                port: 443,
                protocol: 'https',
                sslProtocols: ['TLSv1.2'],
                readTimeout: 60,
                keepaliveTimeout: 5,
                customHeaders: {}
            }
        };

        // 如果需要修改 host header 以匹配新的源

        // 记录修改后的请求头和源信息
        //console.log('Modified headers:', JSON.stringify(request.headers, null, 2));
        //console.log('New origin:', JSON.stringify(request.origin, null, 2));

        return request;
    } catch (error) {
        console.error('Error in handler:', error);
        throw error;
    }
};
