/*
 *   Copyright 2009 Joubin Houshyar
 * 
 *   Licensed under the Apache License, Version 2.0 (the "License");
 *   you may not use this file except in compliance with the License.
 *   You may obtain a copy of the License at
 *    
 *   http://www.apache.org/licenses/LICENSE-2.0
 *    
 *   Unless required by applicable law or agreed to in writing, software
 *   distributed under the License is distributed on an "AS IS" BASIS,
 *   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *   See the License for the specific language governing permissions and
 *   limitations under the License.
 */

package org.jredis.connector;

import java.util.concurrent.Future;
import org.jredis.ClientRuntimeException;
import org.jredis.NotSupportedException;
import org.jredis.ProviderException;
import org.jredis.RedisException;
import org.jredis.protocol.Command;
import org.jredis.protocol.Response;

/**
 * {@link FaultedConnection} is a support class for implementors of JRedis API.
 * 
 * @optional
 * @author  Joubin Houshyar (alphazero@sensesay.net)
 * @version alpha.0, Apr 11, 2009
 * @since   alpha.0
 * 
 */
public class FaultedConnection implements Connection {

	/**  */
	final private String	errorMsg;
	/**  */
	final private ConnectionSpec connSpec;

	/**
	 * instantiates a faulted connection for the given {@link ConnectionSpec}
	 * @param connSpec
	 * @param errMsg
	 */
	public FaultedConnection (ConnectionSpec connSpec, String errMsg) {
		this.errorMsg = errMsg;
		this.connSpec = connSpec;
	}
	/* (non-Javadoc) @see org.jredis.connector.Connection#getModality() */
//	@Override
	public Modality getModality() 
	{
		throw new ClientRuntimeException (errorMsg);
	}

	/* (non-Javadoc) @see org.jredis.connector.Connection#getSpec() */
//	@Override
	public ConnectionSpec getSpec() {
		return connSpec;
	}
	
	/* (non-Javadoc) @see org.jredis.connector.Connection#serviceRequest(org.jredis.protocol.Command, byte[][]) */
//	@Override
	public Response serviceRequest(Command cmd, byte[]... args) throws RedisException, ClientRuntimeException,
			ProviderException 
	{
		throw new ClientRuntimeException (errorMsg);
	}

	/* (non-Javadoc) @see org.jredis.connector.Connection#queueRequest(org.jredis.protocol.Command, byte[][]) */
//	@Override
	public Future<Response> queueRequest(Command cmd, byte[]... args)
			throws ClientRuntimeException, ProviderException 
	{
		throw new ClientRuntimeException (errorMsg);
	}
    /* (non-Javadoc) @see org.jredis.connector.Connection#addListener(org.jredis.connector.Connection.Listener) */
//	@Override
    final public boolean addListener (Listener connListener) {
    	throw new NotSupportedException("Events not supported");
    }
    /* (non-Javadoc) @see org.jredis.connector.Connection#removeListener(org.jredis.connector.Connection.Listener) */
//    @Override
    final public boolean removeListener (Listener connListener) {
    	throw new NotSupportedException("Events not supported");
    }
}
